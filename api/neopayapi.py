import aiohttp
import asyncio
import hashlib
import hmac
import time
import logging
logger = logging.getLogger(__name__)

class ApiClient:
    def __init__(self, bot_id, bot_username, secret_key):
        self.bot_id = bot_id
        self.secret_key = secret_key
        self.bot_username = bot_username
        self.base_url = "https://msa-bff-telegram-neobank.neoflex.ru/v1"

        self.token_cache = {}

    def generate_hash_signature(self, data_string):
        return hmac.new(self.secret_key, data_string.encode(), hashlib.sha256).hexdigest()

    def generate_auth_date(self):
        return str(int(time.time_ns() // 1000000))

    async def get_token(self, chat_id, chat_type, user_id):
        if (chat_id, user_id) in self.token_cache:
            return 200, self.token_cache[(chat_id, user_id)]

        # data_string = (f"bot_id={self.bot_id}\nbot_username={self.bot_username}\nchat_id={chat_id}\n"
        #                f"chat_type={chat_type}\nuser_id={user_id}")

        data_string = (f"bot_id={self.bot_id}\nbot_username={self.bot_username}\nchat_id=583149224\n"
                       f"chat_type={chat_type}\nuser_id={user_id}")
        hash_signature = self.generate_hash_signature(data_string)
        auth_date = self.generate_auth_date()

        params = {
            "bot_id": self.bot_id,
            "bot_username": self.bot_username,
            "chat_id": chat_id,
            "chat_type": chat_type,
            "user_id": user_id,
            "hash": hash_signature,
            "auth_date": auth_date
        }

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=True)) as session:
            async with session.get(f"{self.base_url}/token", params=params) as response:
                if response.status == 200:
                    logger.log(2, await response.json())

                    token_data = await response.json()
                    token = token_data.get("access_token")

                    if token:
                        self.token_cache[(chat_id, user_id)] = token
                        return response.status, token
                else:
                    auth_url = f"{self.base_url}/auth" + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
                    return response.status, auth_url

    async def get_resource(self, endpoint, authorization_token, params=None):
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": "Bearer " + authorization_token}
        params = params or {}
        logger.log(1, url)

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(url, headers=headers, params=params) as response:

                logger.log(2, await response.json())
                return await response.json()

    def get_token_cache(self, key):
        return self.token_cache.get(key)

# class BankApiClient(ApiClient):
#     def __init__(self, bot_id, chat_id, chat_type, user_id, secret_key):
#         super().__init__(bot_id, chat_id, chat_type, user_id, secret_key)
#         self.base_url = "https://msa-bff-telegram-neobank.neoflex.ru/v1"
#
#     async def close_account(self, account_id, authorization_token):
#         url = f"{self.base_url}/accounts/{account_id}/close"
#         headers = {
#             "Authorization": authorization_token,
#         }
#         async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
#             async with session.post(url, headers=headers) as response:
#                 if response.status == 200:
#                     return await response.json()
#                 else:
#                     return await response.json()
#
#     async def get_products(self, authorization_token, product_type):
#         url = f"{self.base_url}/products"
#         headers = {
#             "Authorization": authorization_token,
#         }
#         params = {
#             "productType": product_type
#         }
#         async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
#             async with session.get(url, headers=headers, params=params) as response:
#                 if response.status == 200:
#                     return await response.json()
#                 else:
#                     return await response.json()
#
#     async def open_deposit(self, authorization_token, account_id, deposit_product_id, period, amount,
#                            auto_prolongation):
#         url = f"{self.base_url}/deposits"
#         headers = {
#             "Authorization": authorization_token,
#         }
#         data = {
#             "accountId": account_id,
#             "depositProductId": deposit_product_id,
#             "period": period,
#             "amount": amount,
#             "autoProlongation": auto_prolongation
#         }
#         async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
#             async with session.post(url, headers=headers, json=data) as response:
#                 if response.status == 201:
#                     return await response.json()
#                 else:
#                     return await response.json()
#
#     async def get_deposits(self, authorization_token, status=None):
#         url = f"{self.base_url}/deposits"
#         headers = {
#             "Authorization": authorization_token,
#         }
#         params = {
#             "status": status
#         } if status else {}
#
#         async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
#             async with session.get(url, headers=headers, params=params) as response:
#                 if response.status == 200:
#                     return await response.json()
#                 else:
#                     return await response.json()
#
#     async def close_deposit(self, deposit_id, authorization_token):
#         url = f"{self.base_url}/deposits/{deposit_id}/close"
#         headers = {
#             "Authorization": authorization_token,
#         }
#         async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
#             async with session.post(url, headers=headers) as response:
#                 if response.status == 200:
#                     return await response.json()
#                 else:
#                     return await response.json()


async def main():
    chat_id = 583149224
    bot_username = "neopayment_bot"
    chat_type = "private"
    user_id = 583149224
    bot_id = 7711831733

    secret_key = b"30ec394b126a59742e36d85e44a08cefe3b349cd81e275af97539c0e8acc6897"

    client = ApiClient(bot_id, bot_username, secret_key)
    print(await client.get_token(chat_id, chat_type, user_id))

    # bank_api_client = BankApiClient(bot_id, chat_id, chat_type, user_id, secret_key)

    # account_id = "account_id_to_close"
    # close_account_response = await bank_api_client.close_account(account_id, auth_token)
    # print(close_account_response)
    #
    # products = await bank_api_client.get_products(auth_token, "deposit")
    # print(products)
    #
    # deposit_response = await bank_api_client.open_deposit(auth_token, "account_id", "product_id", 12, 1000, True)
    # print(deposit_response)
    #
    # deposits = await bank_api_client.get_deposits(auth_token, "ACTIVE")
    # print(deposits)
    #
    # deposit_id = "deposit_id_to_close"
    # close_deposit_response = await bank_api_client.close_deposit(deposit_id, auth_token)
    # print(close_deposit_response)


