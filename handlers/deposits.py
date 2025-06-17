from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from content import get_currency_symbol
from filters.filter import TypicalFilter
from keyboards.deposits_kb import get_deposits_kb
from main import api
from models.mock_data import MOCK_DATA
from models.models import DefaultActions, Action, Deposit

router = Router()


@router.message(TypicalFilter(for_replace=["/deposits", "/deposit", "Вклады"]))
async def deposits_handler(message: Message, state: FSMContext):
    deposits = await api.get_deposits(api.try_get_token(message.chat.id), status="ACTIVE")
    print(deposits)

    if not deposits:
        return await message.answer("Сначала пройдите регистрацию /start")

    if deposits and len(deposits) == 0:
        return await message.answer("У вас нет активных вкладов.")

    await state.update_data(items=deposits, current_index=0)

    await message.answer(
        text=format_deposit_info(deposits[0]),
        reply_markup=get_deposits_kb(),
        parse_mode="HTML"
    )

@router.callback_query(DefaultActions.filter(F.action == Action.deposits))
async def account_callback(call: CallbackQuery, state: FSMContext):
    await deposits_handler(call.message, state)

def format_deposit_info(deposit: Deposit):
    return (
        f"<b>💳 <code>{deposit.number}\n</code></b>"
        f"<b>{deposit.name}</b>\n"
        f"<i>{'✔️' if deposit.auto_prolongation else '❌'} Автопродление</i>\n"
        f"📅 С {deposit.start_date} по {deposit.planned_end_date}\n"
        f"💸 {deposit.amount}{get_currency_symbol(deposit.currency_number)} под <b>{deposit.rate}%</b>"
    )