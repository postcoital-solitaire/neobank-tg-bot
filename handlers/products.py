from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from keyboards.products_kb import get_products_kb
from models.mock_data import MOCK_DATA

from filters.filter import IsTextFilter

router = Router()

router.message.filter(
    IsTextFilter(),
)

@router.message(Command("products"))
async def products_handler(message: Message, state: FSMContext):
    products = MOCK_DATA["products"]

    if not products:
        return await message.answer("Нет доступных продуктов.")

    await state.update_data(items=products, current_index=0)

    await message.answer(
        text=format_product_info(products[0]),
        reply_markup=get_products_kb()
    )


@router.callback_query(F.data == "open_selected_product")
async def open_selected_product(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product = data.get("items", [{}])[data.get("current_index", 0)]

    await call.answer(f"Открытие продукта {product.get('name', '')}")


def format_product_info(product):
    return (
        f"Продукт: {product['name']}\n"
        f"Код: {product['code']}\n"
        f"Тип: {product['type']}"
    )