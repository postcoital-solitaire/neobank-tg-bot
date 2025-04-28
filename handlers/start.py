from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from filters.filter import IsTextFilter, TypicalFilter
from keyboards.main_menu import get_open_menu_kb, get_close_menu_kb, get_info_menu_kb
from main import api

from models.models import DefaultActions, Action

router = Router()

router.message.filter(
    IsTextFilter(),
)

@router.message(
    TypicalFilter(for_replace="/start"))
async def checktoken(call_q: CallbackQuery, state: FSMContext):

    _, token = await api.get_token(call_q.from_user.id, call_q.chat.type, call_q.from_user.id)
    print(_)

    if _ != 200:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Авторизация", web_app=WebAppInfo(url=token))]
            ]
        )

        await call_q.answer(
            text=f"Для получения доступа перейдите по ссылке и авторизуйтесь.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть", callback_data=DefaultActions(
                action=Action.open_menu
            ).pack())],
            [InlineKeyboardButton(text="Закрыть", callback_data=DefaultActions(
                action=Action.close_menu
            ).pack())],
            [InlineKeyboardButton(text="Информация", callback_data=DefaultActions(
                action=Action.info_menu
            ).pack())]
        ]
    )

    await call_q.answer(
        text=f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(DefaultActions.filter(F.action == Action.open_menu))
async def open_menu_handler(call: CallbackQuery):
    await call.message.edit_text(
        text="Что вы хотите открыть?",
        reply_markup=get_open_menu_kb()
    )

@router.callback_query(DefaultActions.filter(F.action == Action.close_menu))
async def close_menu_handler(call: CallbackQuery):
    await call.message.edit_text(
        text="Что вы хотите закрыть?",
        reply_markup=get_close_menu_kb()
    )

@router.callback_query(DefaultActions.filter(F.action == Action.info_menu))
async def info_menu_handler(call: CallbackQuery):
    await call.message.edit_text(
        text="О чем вы хотите получить информацию?",
        reply_markup=get_info_menu_kb()
    )