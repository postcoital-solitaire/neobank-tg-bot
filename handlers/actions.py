from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message

from content import get_currency_symbol
from filters.filter import IsTextFilter
from handlers.accounts import accounts_handler
from handlers.deposits import deposits_handler
from main import api
from models.models import OpenStates

router = Router()

router.message.filter(
    IsTextFilter(),
)


@router.callback_query(F.data.startswith(("open_", "close_")))
async def handle_product_actions(call: CallbackQuery, state: FSMContext):
    action = call.data.split("_")[0]
    product_type = call.data.split("_")[1]
    if action == "open":
        await handle_open_action(call, state)
    else:
        await handle_close_action(call, state)


@router.callback_query(F.data.startswith("open_"))
async def handle_open_action(call: CallbackQuery, state: FSMContext):
    product_type = call.data.split("_")[1]
    token = api.try_get_token(call.message.chat.id)

    if not token:
        await call.answer("Сначала авторизуйтесь")
        return

    await state.update_data(current_product_type=product_type)

    if product_type == "account":
        await start_open_account(call, state)
    elif product_type == "deposit":
        #await start_open_deposit(call, state)
        await call.answer("Открытие вклада...")


# === Открытие счета ===
async def start_open_account(call: CallbackQuery, state: FSMContext):
    currencies = [
        {"code": 643, "name": "Рубли (RUB)", "symbol": "₽"},
        {"code": 840, "name": "Доллары (USD)", "symbol": "$"},
        {"code": 978, "name": "Евро (EUR)", "symbol": "€"}
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{curr['name']} {curr['symbol']}",
            callback_data=f"select_currency_{curr['code']}"
        )] for curr in currencies
    ])

    await call.message.edit_text(
        "Выберите валюту счета:",
        reply_markup=kb
    )
    await state.set_state(OpenStates.waiting_account_currency)


@router.callback_query(F.data.startswith("select_currency_"))
async def process_account_currency(call: CallbackQuery, state: FSMContext):
    currency_code = int(call.data.split("_")[-1])
    await state.update_data(currency_number=currency_code)
    await call.message.edit_text(
        "Введите начальную сумму для открытия счета (минимум 1000):"
    )
    await state.set_state(OpenStates.waiting_account_amount)


@router.message(OpenStates.waiting_account_amount)
async def process_account_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 1000:
            raise ValueError
    except ValueError:
        await message.answer("Некорректная сумма. Введите число не менее 1000:")
        return

    data = await state.get_data()

    try:
        result = await api.open_account(
            token=api.try_get_token(message.chat.id),
            currency=data["currency_number"],
            amount=amount
        )

        await message.answer(
            f"✅ Счет успешно открыт!\n\n"
            f"Номер: {result.account_number}\n"
            f"Баланс: {result.amount:.2f} {get_currency_symbol(data['currency_number'])}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")]
            ])
        )
        await state.clear()

    except Exception as e:
        await message.answer(
            f"❌ Ошибка при открытии счета: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Попробовать снова", callback_data="open_account")]
            ])
        )


async def handle_close_action(call: CallbackQuery, product_type: str, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])

    if not items:
        await call.answer("Нет доступных элементов для закрытия")
        return

    current_index = data.get("current_index", 0)
    current_item = items[current_index]

    if product_type == "deposit":
        confirm_text = (
            f"⚠️ Вы уверены, что хотите закрыть вклад?\n\n"
            f"▪ Номер: {current_item.number}\n"
            f"▪ Сумма: {current_item.amount:.2f} ₽\n"
            f"▪ Ставка: {current_item.rate:.2f}%"
        )
        callback_prefix = "confirm_close_deposit"
    elif product_type == "account":
        confirm_text = (
            f"⚠️ Вы уверены, что хотите закрыть счет?\n\n"
            f"▪ Номер: {current_item.account_number}\n"
            f"▪ Баланс: {current_item.amount:.2f} ₽\n"
            f"▪ Доступно: {current_item.available_amount:.2f} ₽"
        )
        callback_prefix = "confirm_close_account"
    else:
        confirm_text = "⚠️ Вы уверены, что хотите закрыть кредит?"
        callback_prefix = "confirm_close_credit"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да",
                callback_data=f"{callback_prefix}_{current_item.id}"
            ),
            InlineKeyboardButton(
                text="❌ Нет",
                callback_data=f"cancel_close_{product_type}"
            )
        ]
    ])

    await call.message.edit_text(
        text=confirm_text,
        reply_markup=kb
    )
    await call.answer()


@router.callback_query(F.data.startswith("confirm_close_"))
async def execute_close(call: CallbackQuery, state: FSMContext):
    action, product_type, item_id = call.data.split("_", 2)
    token = api.try_get_token(call.message.chat.id)

    if not token:
        await call.answer("Авторизация недействительна")
        return

    try:
        if product_type == "deposit":
            await api.close_deposit(token, item_id)

        elif product_type == "account":
            await api.close_account(token, item_id)

        data = await state.get_data()
        items = data.get("items", [])
        items = [item for item in items if item.id != item_id]
        await state.update_data(items=items)

        await show_updated_list(call, product_type, state)

    except Exception as e:
        await call.message.edit_text(
            f"❌ Ошибка при закрытии: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data=f"list_{product_type}")]
            ])
        )


async def show_updated_list(call: CallbackQuery, product_type: str, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])

    if not items:
        await call.message.edit_text(
            "У вас больше нет активных элементов этого типа",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")]
            ]))
        return

    success_msg = "✅ Счет успешно закрыт"

    if product_type == "deposit":
        success_msg = "✅ Вклад успешно закрыт"

    await call.message.answer(text=success_msg)

    if product_type == "deposit":
        await deposits_handler(call.message, state)
    elif product_type == "account":
        await accounts_handler(call.message, state)

    await call.message.delete()


@router.callback_query(F.data.startswith("cancel_close_"))
async def cancel_close(call: CallbackQuery, state: FSMContext):
    product_type = call.data.split("_")[-1]

    if product_type == "deposit":
        await deposits_handler(call.message, state)
    elif product_type == "account":
        await accounts_handler(call.message, state)

    await call.message.delete()