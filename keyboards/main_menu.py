from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup
from models.models import DefaultActions, Action

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Счета"),
                KeyboardButton(text="Вклады"),
                KeyboardButton(text="Кредиты")
            ],
            [
                KeyboardButton(text="Переводы")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False  
    )


def get_auth_kb(url):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Авторизация", web_app=WebAppInfo(url=url))]
        ]
    )