import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config as c
from db import DatabaseManager

dm = DatabaseManager()
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    bot = Bot(token=c.TOKEN_TG)
    await dm.create_pool()

    from handlers import admin_handler
    from handlers.worker import registration_handler, main_handler

    rooters = [registration_handler, main_handler]

    for root in rooters:
        dp.include_router(root.router)

    logging.warning("Бот начал работу")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
