from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery

from filters.filter import IsTextFilter

router = Router()

router.message.filter(
    IsTextFilter(),
)

class NavigationState(StatesGroup):
    current_index = State()
    items = State()

@router.callback_query(F.data.startswith(("prev_", "next_")))
async def navigate_items(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    current_index = data.get("current_index", 0)

    direction = -1 if call.data.startswith("prev_") else 1
    new_index = (current_index + direction) % len(items)

    await state.update_data(current_index=new_index)

    item_type = call.data.split("_")[1]
    await update_item_message(call, items[new_index], item_type)


async def update_item_message(call: CallbackQuery, item, item_type):
    if item_type == "deposit":
        from handlers.deposits import format_deposit_info
        text = format_deposit_info(item)
        from keyboards.deposits_kb import get_deposits_kb
        kb = get_deposits_kb()
    elif item_type == "account":
        from handlers.accounts import format_account_info
        text = format_account_info(item)
        from keyboards.accounts_kb import get_accounts_kb
        kb = get_accounts_kb()
    else:  # product
        from handlers.products import format_product_info
        text = format_product_info(item)
        from keyboards.products_kb import get_products_kb
        kb = get_products_kb()

    await call.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")