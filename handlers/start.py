from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from filters.filter import IsTextFilter, TypicalFilter
from keyboards.main_menu import get_main_kb, get_auth_kb
from main import api, photo_cache

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
        await call_q.answer(
            text=f"Для получения доступа перейдите по ссылке и авторизуйтесь.",
            parse_mode="Markdown",
            reply_markup=get_auth_kb(token)
        )

        return

    photo_id = photo_cache.get("start")

    if photo_id:
        await call_q.answer_photo(
            photo=photo_id,
            caption="Выберите продукт:",
            reply_markup=get_main_kb(),
            parse_mode="HTML"
        )
    else:
        await call_q.answer(
            text="Выберите продукт:",
            reply_markup=get_main_kb(),
            parse_mode="HTML"
        )
