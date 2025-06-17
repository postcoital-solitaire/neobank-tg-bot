from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from content import get_currency_symbol
from filters.filter import IsTextFilter
from handlers.accounts import accounts_handler
from handlers.credits import credits_handler
from handlers.deposits import deposits_handler
from main import api

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
    "credit": credits_handler,
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
    source_currency_id = current_item.currency_number
    amount = getattr(current_item, "amount", 0)

    if amount == 0 or product_type == "deposit":
        await state.update_data(
            product_type=product_type,
            current_index=current_index,
            source_id=current_item.id,
            source_currency_id=source_currency_id
        )

        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить закрытие", callback_data="confirm_transfer_close"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{product_type}")
            ]
        ])
        await call.message.edit_text(
            f"⚠️ Подтвердите закрытие {get_product_name(product_type)}а.",
            reply_markup=confirm_keyboard
        )
        return

    try:
        accounts = await api.get_accounts(token)
        wallets = [acc for acc in accounts if acc.status == "ACTIVE" and acc.id != current_item.id and acc.currency_number == source_currency_id]
        if not wallets:
            await call.message.edit_text(
                "❌ Невозможно закрыть: нет доступных счетов для перевода средств.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="← Назад", callback_data=f"list:{product_type}")]
                ])
            )
            return

        await state.update_data(
            product_type=product_type,
            current_index=current_index,
            account_selection=wallets,
            source_currency_id=source_currency_id
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{acc.account_number} ({acc.amount:.2f} {get_currency_symbol(acc.currency_number)})",
                callback_data=f"select_account_idx:{i}"
            )] for i, acc in enumerate(wallets)
        ])

        await call.message.edit_text(
            "💸 Выберите счёт для перевода средств перед закрытием:",
            reply_markup=keyboard
        )
    except Exception as e:
        await call.message.edit_text(f"❌ Ошибка при загрузке счетов: {e}")

@router.callback_query(F.data.startswith("select_account_idx:"))
async def handle_account_selection(call: CallbackQuery, state: FSMContext):
    index = int(call.data.split(":")[1])
    data = await state.get_data()

    wallets = data.get("account_selection", [])
    if index >= len(wallets):
        await call.answer("⚠️ Неверный выбор")
        return

    selected_account = wallets[index]
    target_id = selected_account.id

    items = data.get("items", [])
    current_index = data.get("current_index", 0)
    source = items[current_index]
    product_type = data.get("product_type")

    await state.update_data(target_account_id=target_id, source_id=source.id)

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_transfer_close"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{product_type}")
        ]
    ])

    await call.message.edit_text(
        f"⚠️ Подтвердите перевод средств и закрытие {get_product_name(product_type)}а",
        reply_markup=confirm_keyboard
    )

@router.callback_query(F.data == "confirm_transfer_close")
async def handle_transfer_and_close(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token = api.try_get_token(call.message.chat.id)

    if not token:
        await call.answer("❌ Требуется авторизация")
        return

    product_type = data.get("product_type", "deposit")
    source_id = data.get("source_id")
    target_id = data.get("target_account_id")

    source_currency_id = data.get("source_currency_id")

    items = data.get("items", [])
    source = next((item for item in items if str(item.id) == str(source_id)), None)
    amount = getattr(source, "amount", 0)

    try:
        if product_type != "deposit":
            await api.transfer_funds(
                token=token,
                from_account_id=source_id,
                to_account_id=target_id,
                amount=amount,
                message=f"Автоматический перевод перед закрытием счета {source_id}"
            )

        if product_type == "deposit":
            await api.close_deposit(token, source_id)
        elif product_type == "account":
            await api.close_account(token, source_id, source_currency_id)

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
    print(product_type)
    if handler:
        await handler(call.message, state)
    else:
        await call.answer("⚠️ Неизвестный тип продукта")
