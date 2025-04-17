from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from filters.filter import IsTextFilter, TypicalFilter
from main import client
from models.models import DefaultActions, Action

router = Router()

router.message.filter(
    IsTextFilter(),
)

@router.message(
    TypicalFilter(for_replace="/start"))
async def checktoken(call_q: CallbackQuery, state: FSMContext):
    _, token = await client.get_token(call_q.from_user.id, call_q.chat.type, call_q.from_user.id)
    print(_)

    if _ != 200:
        auth_link = token
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Авторизация", url=auth_link)]
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
            [InlineKeyboardButton(text="📄 Вклады", callback_data=DefaultActions(
                                              action=Action.deposits).pack()),
             InlineKeyboardButton(text="🎁 Кредиты", callback_data=DefaultActions(
                                              action=Action.credits).pack())],

            [InlineKeyboardButton(text="✨ Счета", callback_data=DefaultActions(
                                              action=Action.accounts).pack()),
             InlineKeyboardButton(text="Продукты", callback_data=DefaultActions(
                                              action=Action.products).pack())]
        ]
    )

    await call_q.answer(
        text=f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
