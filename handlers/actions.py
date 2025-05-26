from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from content import get_currency_symbol
from filters.filter import IsTextFilter
from handlers.accounts import accounts_handler
from handlers.deposits import deposits_handler
from main import api
from models.models import OpenStates

router = Router()
router.message.filter(IsTextFilter())

PRODUCT_NAMES = {
    "deposit": "вклад",
    "account": "счет",
    "credit": "кредит"
}

HANDLERS = {
    "deposit": deposits_handler,
    "account": accounts_handler,
}


def get_product_name(product_type: str) -> str:
    return PRODUCT_NAMES.get(product_type, "продукт")


def get_product_handler(product_type: str):
    return HANDLERS.get(product_type)


@router.callback_query(F.data.startswith("close_"))
async def handle_close_action(call: CallbackQuery, state: FSMContext):
    _, product_type = call.data.split("_", 1)

    token = api.try_get_token(call.message.chat.id)
    if not token:
        await call.answer("❌ Требуется авторизация")
        return

    data = await state.get_data()
    items = data.get("items", [])
    current_index = data.get("current_index", 0)

    if not items:
        await call.answer(f"Нет активных {get_product_name(product_type)}ов для закрытия")
        return

    current_item = items[current_index]

    try:
        accounts = await api.get_accounts(token)
        wallets = [acc for acc in accounts if acc.account_number.startswith("WALLET") and acc.id != current_item.id]

        if not wallets:
            await call.message.edit_text(
                "❌ Невозможно закрыть: нет доступных счетов для перевода средств.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="← Назад", callback_data=f"list:{product_type}")]
                ])
            )
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{acc.account_number} ({acc.amount:.2f} ₽)",
                callback_data=f"select_account:{product_type}:{current_item.id}:{acc.id}"
            )] for acc in wallets
        ])
        await call.message.edit_text(
            "💸 Выберите счёт для перевода средств перед закрытием:",
            reply_markup=keyboard
        )
    except Exception as e:
        await call.message.edit_text(f"❌ Ошибка при загрузке счетов: {e}")


@router.callback_query(F.data.startswith("select_account:"))
async def handle_account_selection(call: CallbackQuery, state: FSMContext):
    _, product_type, source_id, target_id = call.data.split(":")

    await state.update_data(target_account_id=target_id, source_id=source_id, product_type=product_type)

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_transfer_close:{product_type}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{product_type}")
        ]
    ])

    await call.message.edit_text(
        f"⚠️ Подтвердите перевод средств и закрытие {get_product_name(product_type)}а",
        reply_markup=confirm_keyboard
    )


@router.callback_query(F.data.startswith("confirm_transfer_close:"))
async def handle_transfer_and_close(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token = api.try_get_token(call.message.chat.id)

    if not token:
        await call.answer("❌ Требуется авторизация")
        return

    product_type = data.get("product_type")
    source_id = data.get("source_id")
    target_id = data.get("target_account_id")

    items = data.get("items", [])
    source = next((item for item in items if str(item.id) == str(source_id)), None)
    amount = getattr(source, "amount", 0)

    try:
        await api._make_request(
            method="POST",
            endpoint="transfer",
            token=token,
            data={
                "fromAccountId": source_id,
                "toAccountId": target_id,
                "amount": amount,
                "message": "Автоматический перевод перед закрытием"
            }
        )

        # Закрытие продукта
        if product_type == "deposit":
            await api.close_deposit(token, source_id)
        elif product_type == "account":
            await api.close_account(token, source_id)

        await call.answer(f"✅ {get_product_name(product_type).capitalize()} успешно закрыт", show_alert=True)

        updated_items = [item for item in items if str(item.id) != source_id]
        await state.update_data(items=updated_items)
        await show_updated_list(call, product_type, state)

    except Exception as e:
        await call.message.edit_text(
            f"❌ Ошибка при переводе или закрытии: {e}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data=f"list:{product_type}")]
            ])
        )


async def show_updated_list(call: CallbackQuery, product_type: str, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])

    if not items:
        await call.message.edit_text(
            f"🔹 У вас нет активных {get_product_name(product_type)}ов",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")]
            ])
        )
        return

    try:
        await call.message.delete()
    except:
        pass

    handler = get_product_handler(product_type)
    if handler:
        await handler(call.message, state)


@router.callback_query(F.data.regexp(r"^(cancel|list):"))
async def handle_back(call: CallbackQuery, state: FSMContext):
    _, product_type = call.data.split(":")
    handler = get_product_handler(product_type)
    if handler:
        await handler(call.message, state)
    else:
        await call.answer("⚠️ Неизвестный тип продукта")
