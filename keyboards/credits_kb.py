from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_credits_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data="prev_credit"),
             InlineKeyboardButton(text="→", callback_data="next_credit")],
            [InlineKeyboardButton(text="Погасить кредит", callback_data="close_credit")],
            [InlineKeyboardButton(text="График платежей", callback_data="credit_schedule")],

            [InlineKeyboardButton(text="Открыть кредит", callback_data="open_credit")],
        ]
    )

def get_credits_info_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data="prev_credit"),
             InlineKeyboardButton(text="→", callback_data="next_credit")],
            [InlineKeyboardButton(text="Погасить кредит", callback_data="close_credit")],
            [InlineKeyboardButton(text="Инфо по кредиту", callback_data="list:credit")],
            [InlineKeyboardButton(text="Открыть кредит", callback_data="open_credit")],
        ]
    )
