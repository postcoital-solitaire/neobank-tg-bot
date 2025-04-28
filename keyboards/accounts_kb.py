from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_accounts_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="←", callback_data="prev_account"),
             InlineKeyboardButton(text="→", callback_data="next_account")],
            [InlineKeyboardButton(text="Закрыть счет", callback_data="close_account")],
            [InlineKeyboardButton(text="Открыть счет", callback_data="open_account")],
        ]
    )
