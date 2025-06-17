from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from content import CURRENCY
from filters.filter import IsTextFilter, TypicalFilter
from main import api
from models.models import TransferStates

router = Router()
router.message.filter(IsTextFilter())


@router.message(TypicalFilter(for_replace=["/transfers", "Переводы"]))
async def transfers_start(message: Message, state: FSMContext):
    token = api.try_get_token(message.chat.id)
    accounts = await api.get_accounts(token)

    if not accounts or len(accounts) < 2:
        return await message.answer("Для перевода нужно минимум два счёта.")

    await state.update_data(accounts=accounts)
    await state.set_state(TransferStates.choosing_from_account)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{a.account_number} ({a.amount} {CURRENCY.get(a.currency_number)[-1]})",
                callback_data=f"from_{i}"
            )] for i, a in enumerate(accounts)
        ]
    )
    await message.answer("Выберите счёт, с которого хотите перевести средства:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("from_"))
async def choose_from_account(call: CallbackQuery, state: FSMContext):
    index = int(call.data.replace("from_", ""))
    data = await state.get_data()
    accounts = data["accounts"]
    from_account = accounts[index]

    to_accounts = [a for i, a in enumerate(accounts) if i != index]
    await state.update_data(from_account=from_account, to_accounts=to_accounts)
    await state.set_state(TransferStates.choosing_to_account)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{a.account_number} ({a.amount} {CURRENCY.get(a.currency_number)[-1]})",
                callback_data=f"to_{i}"
            )] for i, a in enumerate(to_accounts)
        ]
    )

    await call.message.edit_text("Выберите счёт для зачисления:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("to_"))
async def choose_to_account(call: CallbackQuery, state: FSMContext):
    index = int(call.data.replace("to_", ""))
    data = await state.get_data()

    from_account = data["from_account"]
    to_account = data["to_accounts"][index]

    await state.update_data(to_account=to_account)
    await state.set_state(TransferStates.entering_amount)

    from_currency = CURRENCY.get(from_account.currency_number)[-1]
    to_currency = CURRENCY.get(to_account.currency_number)[-1]

    await call.message.edit_text(
        f"<b>Вы выбрали перевод:</b>\n\n"
        f"💳 Счёт списания:\n"
        f"• Номер: <code>{from_account.account_number}</code>\n"
        f"• Остаток: {from_account.available_amount:.2f} / {from_account.amount:.2f} {from_currency}\n\n"
        f"🏦 Счёт зачисления:\n"
        f"• Номер: <code>{to_account.account_number}</code>\n"
        f"• Остаток: {to_account.available_amount:.2f} / {to_account.amount:.2f} {to_currency}\n\n"
        f"Введите сумму перевода:",
        parse_mode="HTML"
    )



@router.message(TransferStates.entering_amount)
async def enter_transfer_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        return await message.answer("Введите корректную сумму.")

    await state.update_data(amount=amount)
    data = await state.get_data()

    from_acc = data["from_account"]
    to_acc = data["to_account"]
    currency_sign = CURRENCY.get(from_acc.currency_number)[-1]

    await state.set_state(TransferStates.confirming_transfer)
    await message.answer(
        f"Подтверждаете перевод {amount:.2f} {currency_sign} с {from_acc.account_number} на {to_acc.account_number}?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_transfer")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_transfer")]
        ])
    )


@router.callback_query(F.data == "confirm_transfer")
async def confirm_transfer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token = api.try_get_token(call.message.chat.id)

    result = await api.transfer_funds(
        token=token,
        from_account_id=data["from_account"].id,
        to_account_id=data["to_account"].id,
        amount=data["amount"]
    )

    await call.message.edit_text("✅ Перевод успешно выполнен." if result else "❌ Не удалось выполнить перевод.")
    await state.clear()


@router.callback_query(F.data == "cancel_transfer")
async def cancel_transfer(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Перевод отменён.")
