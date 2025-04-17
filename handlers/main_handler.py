import os

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.markdown import hbold, hcode
from pyexpat.errors import messages

from api.neopayapi import ApiClient
from filters.filter import IsTextFilter, TypicalFilter
from dotenv import load_dotenv

from main import client
from models.models import DefaultActions, Action

load_dotenv()

router = Router()

router.message.filter(
    IsTextFilter()
)

@router.callback_query(DefaultActions.filter(F.action == Action.deposits))
async def get_deposits_handler_q(call_q: CallbackQuery, bot: Bot):
    await get_deposits_handler(call_q, bot)

@router.message(TypicalFilter(for_replace="/deposits"))
async def get_deposits_handler(message: Message, bot:Bot, state: FSMContext):
    token = client.get_token_cache((message.from_user.id, message.from_user.id))

    if not token:
        await message.answer("Сначала авторизуйтесь через /start.")
        return

    try:
        deposits = await client.get_resource("deposits", token, {"status": "ACTIVE"})

        if not deposits.get("data"):
            await message.answer("У вас нет депозитов.")
            return

        text = "Ваши депозиты:\n"
        for d in deposits["data"]:
            name = d.get("name", "Без названия")
            amount = d.get("amount", "0")
            text += f"- {name}: {amount}\n"

        await bot.send_message(chat_id=message.from_user.id,
                               text=text,
                               parse_mode="HTML")
        await message.answer()

    except Exception as e:
        await message.answer(f"Ошибка при получении депозитов: {e}")


@router.callback_query(DefaultActions.filter(F.action == Action.products))
async def get_products_q(call_q: CallbackQuery, bot: Bot):
    await get_products_handler(call_q, bot)


@router.message(TypicalFilter(for_replace="/products"))
async def get_products_handler(message: Message, bot: Bot, state: FSMContext):
    token = client.get_token_cache((message.from_user.id, message.from_user.id))

    if not token:
        await message.answer("Сначала авторизуйтесь через /start.")
        return

    try:
        products = await client.get_resource("products", token, {"productType": "DEPOSIT"})

        if not products.get("data"):
            await message.answer("Нет доступных продуктов.")
            return

        text = "Доступные продукты:\n"
        for p in products["data"]:
            text += f"- {p.get('name')} ({p.get('code')})\n"

        await bot.send_message(chat_id=message.from_user.id,
                               text=text,
                               parse_mode="HTML")
        await message.answer()

    except Exception as e:
        await message.answer(f"Ошибка при получении продуктов: {e}")


@router.callback_query(DefaultActions.filter(F.action == Action.accounts))
async def get_accounts_q(call_q: CallbackQuery, bot: Bot):
    await get_accounts(call_q, bot)


@router.message(TypicalFilter(for_replace="/accounts"))
async def get_accounts(message: Message, bot: Bot):
    token = client.get_token_cache((message.from_user.id, message.from_user.id))

    if not token:
        await message.answer("Сначала авторизуйтесь через /start.")
        return
    try:
        data = await client.get_resource("accounts", token)

        if not data:
            await message.answer("ℹ️ У вас пока нет открытых счетов.")
            return

        result = f"<b>💳 Ваши счета:</b>\n"

        for i, acc in enumerate(data, start=1):
            result += (
                f"<b>{i}. <code>{acc['accountNumber']}</code></b>\n"
                f"📅 Открыт: {acc['startDate']} {acc['accountStatus']}\n"
                f"🟢 Доступно: {acc['availableAmount']:.2f}/{acc['amount']:.2f} ¥\n\n"
            )

        await bot.send_message(chat_id=message.from_user.id,
                               text=result,
                               parse_mode="HTML")
        await message.answer()

        return
    except Exception as e:
        await message.answer(f"{data[:50]}: {e}")
