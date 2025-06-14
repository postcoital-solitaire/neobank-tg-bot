import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime

import aiohttp
from dotenv import load_dotenv
from typing import Optional, List, Union

from content import DEPOSIT_OPTIONS
from models.models import Account, DepositProduct, Deposit, Credit, PaymentPlanItem

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
    ) -> (int, int):
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
                    print(token)
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
        print(url)
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
                    currency_number=acc.get("currencyNumber", 643),
                    book=acc.get("book", 0)
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
        response = await self._make_request("POST", "accounts/account", token, data=data)
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

    async def close_account(self, token: str, account_id: str, currency_number: int) -> dict:
        """Закрытие счета"""
        print(account_id)
        return await self._make_request("PUT", f"accounts/close-account", token,
                                        data={"accountId": account_id, "currencyNumber": currency_number})

    async def get_deposit_products(self, token: str) -> List[DepositProduct]:
        """Получение списка депозитных продуктов"""
        params = {"productType": "deposit"}
        data = await self._make_request("GET", "products", token, params=params)
        return [
            DepositProduct(
                id=product["id"],
                name=product["name"],
                deposit_product_status=product["depositProductStatus"],
                branch_id=product["branchId"],
                currency_number=product["currencyNumber"]
            ) for product in data.get("products", {}).get("depositProducts", [])
        ]

    async def get_deposit_options(self, token: str) -> dict:
        """Получение всех доступных опций по вкладам"""
        products = await self.get_deposit_products(token)
        options = {}

        for product in products:
            rates = await self._make_request("GET", f"deposit/product/{product.id}/rates", token)
            options[product.name] = rates.get("rates", [])

        return options

    async def open_deposit_with_option(
            self,
            token: str,
            account_id: str,
            product_name: str,
            option_name: str,
            amount: float,
            auto_prolongation: bool = False
    ) -> Deposit:
        """Открытие вклада с выбором конкретного тарифа"""
        # Получаем все доступные опции
        deposit_options = DEPOSIT_OPTIONS.get(product_name, {})

        if not deposit_options:
            raise ValueError(f"Депозитный продукт '{product_name}' не найден")

        option = deposit_options.get(option_name)
        if not option:
            raise ValueError(f"Опция '{option_name}' не найдена в продукте '{product_name}'")

        products = await self.get_deposit_products(token)
        product_id = None
        for product in products:
            if product.name == product_name:
                print(product)
                product_id = product.id
                break

        if not product_id:
            raise ValueError(f"Не удалось найти ID продукта '{product_name}'")

        data = {
            "accountId": account_id,
            "depositProductId": option["id"],
            "startAmount": amount,
            "depositRate": option["rate"],
            "currencyNumber": 643,
            "period": option["period"],
            "autoProlongation": auto_prolongation
        }

        print(data)
        response = await self._make_request("POST", "deposit", token, data=data)

        return Deposit(
            id=response.get("id", ""),
            number=response.get("depositNumber", ""),
            amount=amount,
            start_date=datetime.now().isoformat(),
            end_date=None,
            planned_end_date="",
            name=product_name,
            product_id=product_id,
            rate=option["rate"],
            period=option["period"],
            auto_prolongation=auto_prolongation,
            status="ACTIVE",
            currency_number=643
        )

    async def get_deposits(self, token: str, status: Optional[str] = None) -> List[Deposit]:
        """Получение списка вкладов клиента"""
        params = {"depositStatus": status} if status else None
        data = await self._make_request("POST", "deposits", token, data=params)

        return [
            Deposit(
                id=dep["id"],
                number=dep["depositNumber"],
                amount=dep["startAmount"],
                start_date=dep["startDepositDate"],
                end_date=dep.get("endDepositDate"),
                planned_end_date=dep["planEndDate"],
                name=dep["depositName"],
                product_id=dep.get("depositProductId"),
                rate=dep["depositRate"],
                period=dep["period"],
                auto_prolongation=dep["prolongation"],
                status=dep["depositStatus"],
                currency_number=dep["currencyNumber"]
            ) for dep in data.get("deposit", [])
        ]

    async def open_deposit(
            self,
            token: str,
            account_id: str,
            product_id: str,
            amount: float,
            period: int,
            currency: int,
            auto_prolongation: bool
    ) -> Deposit:
        """Открытие нового вклада"""
        data = {
            "accountId": account_id,
            "depositProductId": product_id,
            "startAmount": amount,
            "depositRate": 9,
            "currencyNumber": currency,
            "period": period,
            "autoProlongation": auto_prolongation
        }
        response = await self._make_request("POST", "deposit", token, data=data)

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

    async def get_credits(self, token: str, status: Optional[str] = "ACTIVE") -> List[Credit]:
        """Получение списка кредитов клиента"""
        params = {"creditStatus": status} if status else None
        data = await self._make_request("POST", "credits", token, data=params)

        return [
            Credit(
                id=cr["id"],
                number=cr["creditNumber"],
                amount=cr["amount"],
                month_payment=cr["monthPayment"],
                name=cr["creditName"],
                rate=cr["rate"],
                period=cr["period"],
                status=cr["creditStatus"],
                currency_number=cr["currencyNumber"]
            )
            for cr in data.get("credit", [])
        ]

    async def get_credit_payment_plan(self, token: str, credit_id: str) -> Credit:
        """Получение графика платежей по кредиту"""
        raw_data = await self._make_request("GET", f"credit/{credit_id}/paymentPlan", token)

        payment_plan_items = []
        for item in raw_data.get("paymentPlan", []):
            payment_plan_items.append(PaymentPlanItem(
                paymentDate=datetime.strptime(item["paymentDate"], "%d-%m-%Y").date(),
                monthPayment=item["monthPayment"],
                repaymentDept=item["repaymentDept"],
                paymentPercent=item["paymentPercent"],
                balanceAmount=item["balanceAmount"],
                paymentNumber=item["paymentNumber"],
            ))

        credit = Credit(
            id=credit_id,
            number=raw_data.get("creditNumber", ""),
            amount=raw_data.get("amount", 0),
            month_payment=raw_data.get("monthPayment", 0),
            name=raw_data.get("creditName", ""),
            rate=raw_data.get("rate", 0),
            period=raw_data.get("period", 0),
            status=raw_data.get("status", "active"),  # по умолчанию
            currency_number=raw_data.get("currencyNumber", 0),

            client_id=raw_data.get("clientId"),
            account_id=raw_data.get("accountId"),
            start_date=datetime.strptime(raw_data["startCreditDate"], "%d-%m-%Y").date()
            if raw_data.get("startCreditDate") else None,
            end_date=datetime.strptime(raw_data["endCreditDate"], "%d-%m-%Y").date()
            if raw_data.get("endCreditDate") else None,
            total_amount=raw_data.get("totalAmount"),
            paid_in_current_month=raw_data.get("paidInCurrentMonth"),
            payment_plan=payment_plan_items
        )

        return credit

    async def repay_credit_early(self, token: str, credit_id: str, amount: float, currency_number: int) -> dict:
        """Полное досрочное погашение кредита"""
        data = {
            "creditId": credit_id,
            "actionAmount": amount,
            "currencyNumber": currency_number
        }
        return await self._make_request("PUT", "credit/repayment", token, data=data)

    async def get_credit_products(self, token: str) -> List[dict]:
        """Получение списка кредитных продуктов"""
        params = {"productType": "credit"}
        data = await self._make_request("GET", "products", token, params=params)
        return data.get("products", {}).get("creditProducts", [])

    async def calculate_credit_offer(
            self,
            token: str,
            product_id: str,
            amount: float,
            period: int,
            currency: int = 643
    ) -> dict:
        """Расчет условий кредита"""
        data = {
            "creditProductId": product_id,
            "amount": amount,
            "period": period,
            "currencyNumber": currency
        }
        return await self._make_request("POST", "credit/calculation", token, data=data)

    async def open_credit(
            self,
            token: str,
            account_id: str,
            product_id: str,
            amount: float,
            period: int,
            currency: int = 643
    ) -> Credit:
        """Открытие нового кредита"""
        # Сначала получаем расчет условий
        calculation = await self.calculate_credit_offer(
            token=token,
            product_id=product_id,
            amount=amount,
            period=period,
            currency=currency
        )

        # Затем открываем кредит
        data = {
            "accountId": account_id,
            "creditProductId": product_id,
            "amount": amount,
            "rate": calculation["rate"],
            "period": period,
            "currencyNumber": currency
        }

        response = await self._make_request("POST", "credit", token, data=data)

        return Credit(
            id=response["id"],
            number=response["creditNumber"],
            amount=amount,
            month_payment=calculation["monthPayment"],
            name=response.get("creditName", ""),
            rate=calculation["rate"],
            period=period,
            status="ACTIVE",
            currency_number=currency
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
        return await self._make_request("PUT", f"deposit/close-deposit", token, data={"depositId": deposit_id})

    async def close(self):
        """Закрытие сессии"""
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def transfer_funds(
            self,
            token: str,
            from_account_id: str,
            to_account_id: str,
            amount: float,
            message: str = ""
    ) -> dict:
        """Перевод средств между счетами"""
        return await self._make_request("POST",
                                        "transfers",
                                        token, data={
                "fromAccountId": from_account_id,
                "toAccountId": to_account_id,
                "amount": amount,
                "message": message
            })

    async def close_deposit_with_transfer(self, token: str, deposit_id: str, target_wallet_id: str) -> dict:
        """Закрытие вклада с переводом на выбранный счёт"""
        return await self._make_request(
            "PUT",
            f"deposit/close-deposit",
            token,
            data={"depositId": deposit_id, "payoutAccountId": target_wallet_id}
        )


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

    try:
        status, token = await api.get_token(
            chat_id=583149224,
            chat_type="private",
            user_id=583149224,
        )

        if status != 200:
            print(f"Auth required: {token}")
            return

        # new_account = await api.open_account(token, currency=643, amount=1000)
        # print("New account:", new_account)
        #
        accounts = [account for account in await api.get_accounts(token) if account.book == 0]
        print("Accounts:", accounts)

        # credits = await api.get_credits(token, status="ACTIVE")
        # print("Active credits:", credits)

        # deposits = await api.get_deposits(token, status="ACTIVE")
        # print("Active deposits:", deposits)
        #
        # products = await api.get_deposit_products(token)
        # print("Deposit products:", products)
        #
        # print(token)
        # if accounts:
        #     account = accounts[2]
        #     deposit = await api.open_deposit_with_option(
        #         token=token,
        #         account_id=account.id,
        #         product_name="Идеальный старт",
        #         option_name="6 месяцев: 7.5%",
        #         amount=50000,
        #         auto_prolongation=True
        #     )
        #     print("New deposit:", deposit)

        # print(await api.transfer_funds(
        #     token=token,
        #     from_account_id=accounts[-2].id,
        #     to_account_id=accounts[0].id,
        #     amount=295997.89
        # ))

        account = accounts[0]


        credit_products = await api.get_credit_products(token)
        print("Доступные кредитные продукты:")
        for i, product in enumerate(credit_products, 1):
            print(f"{i}. {product['name']} (ID: {product['id']})")

        selected_product = credit_products[0]

        amount = 100000
        period = 12

        calculation = await api.calculate_credit_offer(
            token=token,
            product_id=selected_product["id"],
            amount=amount,
            period=period
        )

        credit = await api.open_credit(
            token=token,
            account_id=account.id,
            product_id=selected_product["id"],
            amount=amount,
            period=period
        )
        print(f"New credit:", credit)
        
        # account = await api.open_account(
        #             token=token,
        #             currency=643,
        #             amount=500,
        #         )
        # print("New account:", account)

        # if deposits:
        #     result = await api.close_deposit(token, deposits[0].id)
        #     print("Deposit closed:", result)

    finally:
        await api.close()


if __name__ == '__main__':
    asyncio.run(main())
