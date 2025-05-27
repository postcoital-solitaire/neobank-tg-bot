from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from models.models import DefaultActions, Action

def get_main_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Счета", callback_data=DefaultActions(action=Action.accounts).pack())],
            [InlineKeyboardButton(text="Вклады", callback_data=DefaultActions(action=Action.deposits).pack())],
        ]
    )

def get_auth_kb(url):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Авторизация", web_app=WebAppInfo(url=url))]
        ]
    )