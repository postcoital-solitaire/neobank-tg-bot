from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from filters.filter import IsTextFilter, TypicalFilter
from keyboards.transfers_kb import get_transfers_kb
from main import api
from models.models import DefaultActions, Action, TransferStates
from content import currency

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

