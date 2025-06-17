import asyncio
import importlib
import logging
import os
from typing import List

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from api.neopayapi import NeoBankAPI

#dm = DatabaseManager()
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

from dotenv import load_dotenv
load_dotenv()

bot_username = "neopayment_bot"
bot_id = 7711831733
secret_key = os.getenv("SECRET_KEY")
photo_cache = {}

load_dotenv()

api = NeoBankAPI(bot_id=bot_id,
                 bot_username=bot_username,
                 secret_key=str.encode(secret_key))

class RouterLoader:
    @staticmethod
    def load_routers(dp: Dispatcher, router_modules: List[str]):
        for module_path in router_modules:
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, 'router'):
                    dp.include_router(module.router)
            except ImportError as e:
                logging.error(f"{module_path}: {e}")

    @classmethod
    def load_from_folder(cls, dp: Dispatcher, folder: str = "handlers"):
        router_modules = []
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith('.py') and not file.startswith('_'):
                    rel_path = os.path.relpath(root, os.path.dirname(__file__))
                    module_name = f"{rel_path.replace(os.sep, '.')}.{file[:-3]}"
                    router_modules.append(module_name)
        cls.load_routers(dp, router_modules)


async def main():
    bot = Bot(token=os.getenv("TOKEN_TG"))
    await api.initialize_session()

    #await dm.create_pool()

    # prod
    # RouterLoader.load_routers(dp, [
    #     "handlers.start",
    #     "handlers.deposits",
    #     "handlers.accounts",
    #     "handlers.credits"
    #     "handlers.navigation",
    #     "handlers.actions",
    #     "handlers.help",
    #     "handlers.transfers",
    #     "handlers.image_collector",
    #     "handlers.webapp",
    # ])

    # #dev
    RouterLoader.load_from_folder(dp)

    logging.warning("Бот начал работу")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
