import aiohttp
import asyncio
import hashlib
import hmac
import time

class ApiClient:
    def __init__(self, bot_id, chat_id, chat_type, user_id, bot_username, secret_key):
        self.bot_id = bot_id
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.user_id = user_id
        self.secret_key = secret_key
        self.bot_username = bot_username
        self.base_url = "https://msa-bff-telegram-neobank.neoflex.ru/v1/token"

    def generate_hash_signature(self, data_string):
        return hmac.new(self.secret_key, data_string.encode(), hashlib.sha256).hexdigest()

    def generate_auth_date(self):
        return str(int(time.time()))

    async def get_token(self):
        data_string = f"{self.chat_id}{self.chat_type}{self.user_id}{self.bot_id}{self.bot_username}"
        hash_signature = self.generate_hash_signature(data_string)
        auth_date = self.generate_auth_date()

        params = {
            "chat_id": self.chat_id,
            "chat_type": self.chat_type,
            "user_id": self.user_id,
            "bot_id": self.bot_id,
            "bot_username": self.bot_username,
            "hash": hash_signature,
            "auth_date": auth_date
        }

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(self.base_url, params=params) as response:
                print(params)
                if response.status == 200:
                    print(await response.text())

                    return await response.json()
                else:
                    print(f"{response.text}")
                    return None


class BankApiClient(ApiClient):
    def __init__(self, bot_id, chat_id, chat_type, user_id, secret_key):
        super().__init__(bot_id, chat_id, chat_type, user_id, secret_key)
        self.base_url = "https://msa-bff-telegram-neobank.neoflex.ru/v1"

    async def close_account(self, account_id, authorization_token):
        url = f"{self.base_url}/accounts/{account_id}/close"
        headers = {
            "Authorization": authorization_token,
        }
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return await response.json()

    async def get_products(self, authorization_token, product_type):
        url = f"{self.base_url}/products"
        headers = {
            "Authorization": authorization_token,
        }
        params = {
            "productType": product_type
        }
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return await response.json()

    async def open_deposit(self, authorization_token, account_id, deposit_product_id, period, amount,
                           auto_prolongation):
        url = f"{self.base_url}/deposits"
        headers = {
            "Authorization": authorization_token,
        }
        data = {
            "accountId": account_id,
            "depositProductId": deposit_product_id,
            "period": period,
            "amount": amount,
            "autoProlongation": auto_prolongation
        }
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    return await response.json()

    async def get_deposits(self, authorization_token, status=None):
        url = f"{self.base_url}/deposits"
        headers = {
            "Authorization": authorization_token,
        }
        params = {
            "status": status
        } if status else {}

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return await response.json()

    async def close_deposit(self, deposit_id, authorization_token):
        url = f"{self.base_url}/deposits/{deposit_id}/close"
        headers = {
            "Authorization": authorization_token,
        }
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return await response.json()


# Example usage
async def main():
    bot_id = 7711831733
    bot_username = "neopayment_bot"
    chat_id = "359453249"
    chat_type = "private"
    user_id = "359453249"
    secret_key = b"AAEmec8Bj2BQ6t8kR6ZfjMHlfOLFeXpP9WM"

    client = ApiClient(bot_id, chat_id, chat_type, user_id, bot_username, secret_key)
    print(await client.get_token())
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


# Run the example
asyncio.run(main())
