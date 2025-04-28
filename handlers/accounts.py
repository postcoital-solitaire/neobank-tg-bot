from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from content import currency
from filters.filter import IsTextFilter, TypicalFilter
from keyboards.accounts_kb import get_accounts_kb
from main import api
from models.models import DefaultActions, Action

router = Router()

router.message.filter(
    IsTextFilter(),
)

@router.message(TypicalFilter(for_replace=["/accounts", "/accounts"]))
async def accounts_handler(message: Message, state: FSMContext):
    print(api.try_get_token(message.chat.id))
    accounts = await api.get_accounts(api.try_get_token(message.chat.id))

    if not accounts:
        return await message.answer("Сначала пройдите регистрацию /start")

    if accounts and len(accounts) == 0:
        return await message.answer("У вас нет активных счетов.")

    await state.update_data(items=accounts, current_index=0)

    await message.answer(
        text=format_account_info(accounts[0]),
        reply_markup=get_accounts_kb(),
        parse_mode="HTML"
    )

@router.callback_query(DefaultActions.filter(F.action == Action.accounts))
async def account_callback(call: CallbackQuery, state: FSMContext):
    await accounts_handler(call.message, state)


@router.callback_query(DefaultActions.filter(F.action == Action.close_current_account))
async def close_current_account(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    account = data.get("items", [{}])[data.get("current_index", 0)]

    await api.close_account(api.try_get_token(call.message.chat.id), )


    await call.answer(f"Закрытие счета {account.get('accountNumber', '')}")


def format_account_info(account):
    return (
        f"<b>💳 <code>{account.account_number}\n</code></b>"
        f"📅 Открыт {account.start_date} {account.status}\n"
        f"🟢 Доступно: {account.available_amount} / {account.amount}\n {currency.get(account.currency_number)[-1]}"
    )