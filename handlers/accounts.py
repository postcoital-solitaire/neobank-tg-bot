from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from content import CURRENCY
from filters.filter import IsTextFilter, TypicalFilter
from keyboards.accounts_kb import get_accounts_kb
from main import api
from models.models import DefaultActions, Action

router = Router()

router.message.filter(
    IsTextFilter(),
)

@router.message(TypicalFilter(for_replace=["/accounts", "/accounts", "Счета"]))
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

@router.message(F.text.regexp(r"^/account\s+(\d+)$"))
async def specific_account_handler(message: Message, state: FSMContext):
    token = api.try_get_token(message.chat.id)
    if not token:
        return await message.answer("Сначала пройдите регистрацию /start")

    account_number = message.text.split()[1]
    accounts = await api.get_accounts(token)

    if not accounts:
        return await message.answer("У вас нет активных счетов.")
    await state.update_data(items=accounts, current_index=0)

    matched_account = next((acc for acc in accounts if acc.account_number == account_number), None)

    if not matched_account:
        return await message.answer(f"Счёт с номером {account_number} не найден.")

    await message.answer(
        text=format_account_info(matched_account),
        reply_markup=get_accounts_kb(),
        parse_mode="HTML"
    )

@router.callback_query(DefaultActions.filter(F.action == Action.accounts))
async def account_callback(call: CallbackQuery, state: FSMContext):
    await accounts_handler(call.message, state)


def format_account_info(account):
    return (
        f"<b>💳 <code>{account.account_number}\n</code></b>"
        f"📅 Открыт {account.start_date} {account.status}\n"
        f"🟢 Доступно: {account.available_amount} / {account.amount}\n {CURRENCY.get(account.currency_number)[-1]}"
    )