from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from models.models import DefaultActions, Action

def get_main_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть", callback_data="open_menu")],
            [InlineKeyboardButton(text="Закрыть", callback_data="close_menu")],
            [InlineKeyboardButton(text="Информация", callback_data="info_menu")]
        ]
    )

def get_open_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Счёт", callback_data="open_account")],
            [InlineKeyboardButton(text="Вклад", callback_data="open_deposit")],
            [InlineKeyboardButton(text="Кредит", callback_data="open_credit")]
        ]
    )

def get_close_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Счёт", callback_data="close_account")],
            [InlineKeyboardButton(text="Вклад", callback_data="close_deposit")],
        ]
    )

def get_info_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Счета", callback_data=DefaultActions(action=Action.accounts).pack())],
            [InlineKeyboardButton(text="Вклады", callback_data=DefaultActions(action=Action.deposits).pack())],
        ]
    )

def get_auth_kb(url):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Авторизация", url=url)]
        ]
    )