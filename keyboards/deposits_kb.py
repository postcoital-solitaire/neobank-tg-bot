from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_deposits_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data="prev_deposit"),
             InlineKeyboardButton(text="→", callback_data="next_deposit")],
            [InlineKeyboardButton(text="Открыть вклад", callback_data="open_deposit")],
            [InlineKeyboardButton(text="Закрыть вклад", callback_data="close_current_deposit")]
        ]
    )