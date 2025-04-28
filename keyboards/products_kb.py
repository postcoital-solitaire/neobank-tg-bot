from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_products_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data="prev_product"),
             InlineKeyboardButton(text="→", callback_data="next_product")],
            [InlineKeyboardButton(text="Открыть продукт", callback_data="open_selected_product")]
        ]
    )