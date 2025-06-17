from aiogram import Router
from aiogram.types import Message

from filters.filter import IsTextFilter, TypicalFilter

router = Router()

router.message.filter(
    IsTextFilter(),
)

@router.message(TypicalFilter(for_replace=["/help", "/info", "/faq"]))
async def help_handler(message: Message):
    help_text = (
        "Помощь по боту:\n\n"
        "Основные команды:\n"
        "/start - начать работу с ботом\n"
        "/deposits - управление вкладами\n"
        "/accounts - управление счетами\n"
        "/credits - управление кредитами\n"
        "/webapp - вебапа на моке\n\n"
        "Вы можете:\n"
        "- Открывать и закрывать счета, вклады, кредиты\n"
        "- Просматривать информацию о своих продуктах\n"
        "- Управлять ими через интерактивное меню\n\n"
        "Для навигации используйте кнопки в меню."
    )
    await message.answer(help_text)