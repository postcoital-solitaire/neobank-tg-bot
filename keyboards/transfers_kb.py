from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_transfers_kb(accounts):
    keyboard = []

    for acc in accounts:
        button = InlineKeyboardButton(
            text=f"{acc.account_number} ({acc.available_amount})",
            callback_data=f"transfer_from:{acc.id}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
