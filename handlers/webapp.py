from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from filters.filter import IsTextFilter, TypicalFilter

router = Router()
router.message.filter(IsTextFilter())


@router.message(TypicalFilter(for_replace=["/setmenubutton", "вебапп", "/webapp"]))
async def webapp_start(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Вебапа", web_app=WebAppInfo(url="https://lively-cranachan-dffc27.netlify.app/"))]
        ]
    )
    await message.answer("Перейдите:", reply_markup=keyboard)

