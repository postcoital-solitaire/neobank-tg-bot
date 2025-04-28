from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from filters.filter import TypicalFilter
from keyboards.deposits_kb import get_deposits_kb
from main import api
from models.mock_data import MOCK_DATA
from models.models import DefaultActions, Action

router = Router()


@router.message(TypicalFilter(for_replace=["/deposits", "/deposit"]))
async def deposits_handler(message: Message, state: FSMContext):
    deposits = await api.get_deposits(api.try_get_token(message.chat.id))
    print(deposits)

    if not deposits:
        return await message.answer("Сначала пройдите регистрацию /start")

    if deposits and len(deposits) == 0:
        return await message.answer("У вас нет активных вкладов.")

    await state.update_data(items=deposits, current_index=0)

    await message.answer(
        text=format_deposit_info(deposits[0]),
        reply_markup=get_deposits_kb()
    )

@router.callback_query(DefaultActions.filter(F.action == Action.deposits))
async def account_callback(call: CallbackQuery, state: FSMContext):
    await deposits_handler(call.message, state)

def format_deposit_info(deposit):
    return (
        f"Вклад: {deposit['name']}\n"
        f"Сумма: {deposit['amount']}\n"
        f"Статус: {deposit['status']}"
    )