import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional, Union, List
from datetime import datetime, date

import aiohttp
from dotenv import load_dotenv
from models.models import Deposit, Credit, PaymentPlanItem

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
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, token: str, params: dict = None, data: dict = None) -> dict:
        await self.initialize_session()
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with self.session.request(method, url, headers=headers, params=params, json=data) as response:
                try:
                    response_data = await response.json()
                except aiohttp.ContentTypeError:
                    text = await response.text()
                    response_data = json.loads(text) if text else {}

                if response.status >= 400:
                    error_msg = response_data.get("errorDetail", "Unknown error")
                    raise Exception(f"API error {response.status}: {error_msg}")

                return response_data
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    async def get_deposits(self, token: str, status: Optional[str] = None) -> List[Deposit]:
        params = {"depositStatus": status} if status else None
        data = await self._make_request("GET", "deposits", token, data=params)
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

    async def get_credits(self, token: str, status: Optional[str] = "ACTIVE") -> List[Credit]:
        params = {"creditStatus": status} if status else None
        data = await self._make_request("GET", "credits", token, data=params)
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
            ) for cr in data.get("credit", [])
        ]

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


@dataclass
class DepositProduct:
    id: str
    name: str
    deposit_product_status: str
    branch_id: int
    currency_number: int

@dataclass
class Deposit:
    id: str
    number: str
    amount: float
    start_date: str
    end_date: Optional[str]
    planned_end_date: str
    name: str
    product_id: str
    rate: float
    period: int
    auto_prolongation: bool
    status: str
    currency_number: int

@dataclass
class PaymentPlanItem:
    paymentDate: date
    monthPayment: float
    repaymentDept: float
    paymentPercent: float
    balanceAmount: float
    paymentNumber: int


@dataclass
class Credit:
    id: str
    number: str
    amount: float
    month_payment: float
    name: str
    rate: float
    period: int
    status: str
    currency_number: int

    client_id: Optional[str] = None
    account_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_amount: Optional[float] = None
    paid_in_current_month: Optional[bool] = None
    payment_plan: List[PaymentPlanItem] = field(default_factory=list)


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

        credits = await api.get_credits(token, status="ACTIVE")
        print("Active credits:", credits)

        deposits = await api.get_deposits(token, status="ACTIVE")
        print("Active deposits:", deposits)
    except:
        pass



if __name__ == '__main__':
    asyncio.run(main())
