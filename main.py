import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config as c
from api.neopayapi import ApiClient
from db import DatabaseManager

#dm = DatabaseManager()
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

from dotenv import load_dotenv
load_dotenv()

bot_username = "neopayment_bot"
bot_id = 7711831733
secret_key = os.getenv("SECRET_KEY")

client = ApiClient(bot_id, bot_username, str.encode(secret_key))

async def main():
    bot = Bot(token=os.getenv("TOKEN_TG"))
    #await dm.create_pool()

    from handlers import registration_handler, main_handler

    rooters = [registration_handler, main_handler]

    for root in rooters:
        dp.include_router(root.router)

    logging.warning("Бот начал работу")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
