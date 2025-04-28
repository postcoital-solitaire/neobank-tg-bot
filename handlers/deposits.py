from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.deposits_kb import get_deposits_kb
from models.mock_data import MOCK_DATA

router = Router()


@router.message(Command("deposits"))
async def deposits_handler(message: Message):
    deposits = MOCK_DATA["deposits"]

    if not deposits:
        return await message.answer("У вас нет активных вкладов.")

    await message.answer(
        text=format_deposit_info(deposits[0]),
        reply_markup=get_deposits_kb()
    )


def format_deposit_info(deposit):
    return (
        f"Вклад: {deposit['name']}\n"
        f"Сумма: {deposit['amount']}\n"
        f"Статус: {deposit['status']}"
    )