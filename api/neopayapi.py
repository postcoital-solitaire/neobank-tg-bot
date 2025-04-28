import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
import aiohttp
from dotenv import load_dotenv
from typing import Optional, List, Union
from models.models import Account, DepositProduct, Deposit

logger = logging.getLogger(__name__)

class NeoBankAPI:
    def __init__(self, bot_id: int, bot_username: str, secret_key: bytes):
        self.bot_id = bot_id
        self.bot_username = bot_username
        self.secret_key = secret_key
        self.base_url = "https://msa-bff-telegram-neobank.neoflex.ru/v1"
        self.token_cache = {}
        self.session = None

    def _generate_signature(self, data_string: str) -> str:
        return hmac.new(self.secret_key, data_string.encode(), hashlib.sha256).hexdigest()

    async def initialize_session(self):
        self.session = aiohttp.ClientSession()

    async def get_token(
            self,
            chat_id: Union[str, int],
            chat_type: str,
            user_id: int,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            username: Optional[str] = None
    ) -> tuple[int, str]:
        """Получение токена авторизации"""
        cache_key = (chat_id, user_id)
        if cache_key in self.token_cache:
            return 200, self.token_cache[cache_key]

        auth_date = str(int(time.time_ns() // 1_000_000))

        params = {
            "bot_id": self.bot_id,
            "bot_username": self.bot_username,
            "chat_id": str(chat_id),
            "chat_type": chat_type,
            "user_id": user_id,
            "auth_date": auth_date
        }

        data_string = (
            f"bot_id={self.bot_id}\n"
            f"bot_username={self.bot_username}\n"
            f"chat_id={chat_id}\n"
            f"chat_type={chat_type}\n"
            f"user_id={user_id}"
        )

        params["hash"] = self._generate_signature(data_string)
        print(params)
        if self.session is None:
            await self.initialize_session()
        try:
            async with self.session.get(
                    f"{self.base_url}/token",
                    params=params,
                    allow_redirects=False
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    if token:
                        self.token_cache[cache_key] = token
                        return 200, token
                auth_url = f"{self.base_url}/auth" + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
                return 301, auth_url

        except Exception as e:
            logger.error(f"Token request failed: {str(e)}")
            raise

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        token: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None
    ) -> dict:
        """Базовый метод для выполнения запросов"""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data
            ) as response:
                try:
                    response_data = await response.json()
                except aiohttp.ContentTypeError:
                    text = await response.text()
                    try:
                        response_data = json.loads(text) if text else {}
                    except json.JSONDecodeError:
                        response_data = {"raw_response": text}

                if response.status >= 400:
                    error_msg = response_data.get("errorDetail",
                                               response_data.get("raw_response",
                                                               "Unknown error"))
                    raise Exception(f"API error {response.status}: {error_msg}")

                return response_data
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise


    async def get_accounts(self, token: str) -> List[Account]:
        """Получение списка счетов клиента"""
        try:
            data = await self._make_request("GET", "accounts", token)

            if "accounts" in data:
                accounts = data["accounts"]
            elif isinstance(data, list):
                accounts = data
            else:
                accounts = []

            return [
                Account(
                    id=acc.get("id", ""),
                    account_number=acc.get("accountNumber", ""),
                    amount=acc.get("amount", 0),
                    available_amount=acc.get("availableAmount", 0),
                    start_date=acc.get("startDate", ""),
                    end_date=acc.get("endDate"),
                    status=acc.get("accountStatus", "UNKNOWN"),
                    currency_number=acc.get("currencyNumber", 643)
                ) for acc in accounts
            ]
        except Exception as e:
            logger.error(f"Failed to get accounts: {str(e)}")
            raise Exception(f"Не удалось получить список счетов: {str(e)}")

    async def open_account(self, token: str, currency: int, amount: float) -> Account:
        """Открытие нового счета"""
        data = {
            "currencyNumber": currency,
            "amount": amount
        }
        response = await self._make_request("POST", "accounts", token, data=data)
        return Account(
            id=response["accountId"],
            account_number=response["accountNumber"],
            amount=response["amount"],
            available_amount=response["amount"],
            start_date=response["startDate"],
            end_date=None,
            status="ACTIVE",
            currency_number=response["currencyNumber"]
        )

    async def close_account(self, token: str, account_id: str) -> dict:
        """Закрытие счета"""
        return await self._make_request("POST", f"accounts/{account_id}/close", token)

    # Products methods
    async def get_deposit_products(self, token: str) -> List[DepositProduct]:
        """Получение списка депозитных продуктов"""
        params = {"productType": "deposit"}
        data = await self._make_request("GET", "products", token, params=params)
        return [
            DepositProduct(
                product_id=product["productId"],
                name=product["depositName"],
                min_amount=product["minAmount"],
                max_amount=product["maxAmount"],
                rate=product["depositRate"],
                min_period=product["minPeriod"],
                max_period=product["maxPeriod"],
                currency_number=product["currencyNumber"]
            ) for product in data.get("products", {}).get("deposits", [])
        ]

    async def get_deposits(self, token: str, status: Optional[str] = None) -> List[Deposit]:
        """Получение списка вкладов клиента"""
        params = {"status": status} if status else None
        data = await self._make_request("GET", "deposits", token, params=params)
        return [
            Deposit(
                id=dep["id"],
                number=dep["depositNumber"],
                amount=dep["amount"],
                start_date=dep["startDepositDate"],
                end_date=dep.get("endDepositDate"),
                planned_end_date=dep["planEndDate"],
                name=dep["depositName"],
                product_id=dep["depositProductId"],
                rate=dep["depositRate"],
                period=dep["period"],
                auto_prolongation=dep["prolongation"],
                status=dep["status"],
                currency_number=dep["currency_number"]
            ) for dep in data.get("deposit", [])
        ]

    async def open_deposit(
            self,
            token: str,
            account_id: str,
            product_id: str,
            amount: float,
            period: int,
            auto_prolongation: bool
    ) -> Deposit:
        """Открытие нового вклада"""
        data = {
            "accountId": account_id,
            "depositProductId": product_id,
            "amount": amount,
            "period": period,
            "autoProlongation": auto_prolongation
        }
        response = await self._make_request("POST", "deposits", token, data=data)

        print(data)
        return Deposit(
            id=response.get("id", ""),
            number=response["deposit_number"],
            amount=amount,
            start_date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            end_date=None,
            planned_end_date="",
            name="",
            product_id=product_id,
            rate=0,
            period=period,
            auto_prolongation=auto_prolongation,
            status="ACTIVE",
            currency_number=643
        )

    def try_get_token(self, id: int):
        return self.token_cache.get((id, id), None)

    async def _get_auth_url(
            self,
            chat_id: Union[str, int],
            chat_type: str,
            user_id: int,
    ) -> str:

        auth_date = str(int(time.time_ns() // 1_000_000))

        params = {
            "bot_id": self.bot_id,
            "bot_username": self.bot_username,
            "chat_id": str(chat_id),
            "chat_type": chat_type,
            "user_id": user_id,
            "auth_date": auth_date
        }

        data_string = (
            f"bot_id={self.bot_id}\n"
            f"bot_username={self.bot_username}\n"
            f"chat_id={chat_id}\n"
            f"chat_type={chat_type}\n"
            f"user_id={user_id}"
        )

        params["hash"] = self._generate_signature(data_string)
        return f"{self.base_url}/auth" + "?" + "&".join([f"{key}={value}" for key, value in params.items()])

    async def close_deposit(self, token: str, deposit_id: str) -> dict:
        """Закрытие вклада"""
        return await self._make_request("POST", f"deposits/{deposit_id}/close", token)

    async def close(self):
        """Закрытие сессии"""
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()





async def main():
    load_dotenv()

    bot_username = "neopayment_bot"
    bot_id = 7711831733
    secret_key = os.getenv("SECRET_KEY")

    api = NeoBankAPI(bot_id=bot_id,
                     bot_username=bot_username,
                     secret_key=str.encode(secret_key))

    url = await api._get_auth_url(
            chat_id=583149224,
            chat_type="private",
            user_id=583149224
    )
    print(url)

    # try:
        # status, token = await api.get_token(
        #     chat_id=583149224,
        #     chat_type="private",
        #     user_id=583149224,
        # )
        #
        # if status != 200:
        #     print(f"Auth required: {token}")
        #     return


        # new_account = await api.open_account(token, currency=643, amount=1000)
        # print("New account:", new_account)
        #
        # accounts = await api.get_accounts(token)
        # print("Accounts:", accounts)

        # deposits = await api.get_deposits(token, status="ACTIVE")
        # print("Active deposits:", deposits)
        #
        # products = await api.get_deposit_products(token)
        # print("Deposit products:", products)

        # if accounts and products:
        #     deposit = await api.open_deposit(
        #         token=token,
        #         account_id=accounts[0].id,
        #         product_id=products[0].product_id,
        #         amount=500,
        #         period=12,
        #         auto_prolongation=True
        #     )
        #     print("New deposit:", deposit)

        # if deposits:
        #     result = await api.close_deposit(token, deposits[0].id)
        #     print("Deposit closed:", result)

    # finally:
    #     await api.close()


if __name__ == '__main__':
    asyncio.run(main())
