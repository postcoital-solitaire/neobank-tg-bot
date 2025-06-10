from typing import List

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from content import currency, send_long_message
from filters.filter import IsTextFilter, TypicalFilter
from keyboards.credits_kb import get_credits_kb, get_credits_info_kb
from main import api
from models.models import DefaultActions, Action, Credit

router = Router()

router.message.filter(IsTextFilter())

@router.message(TypicalFilter(for_replace=["/credits", "/credits", "Кредиты"]))
async def credits_handler(message: Message, state: FSMContext):
    token = api.try_get_token(message.chat.id)
    data = await state.get_data()
    credits = data.get("items", await api.get_credits(token, "ACTIVE"))

    if not isinstance(credits, list) or not all(isinstance(c, Credit) for c in credits):
        credits = await api.get_credits(token, "ACTIVE")

    if not token:
        return await message.answer("Сначала пройдите регистрацию /start")

    if not credits or len(credits) == 0:
        return await message.answer("У вас нет активных кредитов.")

    index = data.get("current_index", 0)

    await state.update_data(items=credits, current_index=index)

    credit = credits[index]

    await message.answer(
        text=format_credit_info(credit),
        reply_markup=get_credits_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "credit_schedule")
async def credit_schedule_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    credits = data.get("items", [])
    index = data.get("current_index", 0)

    if not credits:
        await call.answer("Нет доступных кредитов.")
        return

    credit = credits[index]
    token = api.try_get_token(call.message.chat.id)
    await state.update_data(items=credits, current_index=index)

    updated_credit = await api.get_credit_payment_plan(token, credit.id)
    if not updated_credit or not updated_credit.payment_plan:
        return await call.message.edit_text("📭 Нет данных по расчетам.")

    lines = [
        f"<b>💸 График платежей по кредиту <code>{updated_credit.number}</code>:</b>\n"
    ]
    for p in updated_credit.payment_plan:
        lines.append(
            f"📅 {p.paymentDate.strftime('%d.%m.%Y')}: {p.monthPayment:.2f} "
            f"({p.paymentPercent:.2f} — проценты, {p.repaymentDept:.2f} — тело)"
        )

    await send_long_message(
        text="\n".join(lines),
        bot=call.message.bot,
        chat_id=call.message.chat.id,
        reply_markup=get_credits_info_kb(),
        parse_mode="HTML"
    )


@router.callback_query(DefaultActions.filter(F.action == Action.credits))
async def credit_callback(call: CallbackQuery, state: FSMContext):
    await credits_handler(call.message, state)


def format_credit_info(credit):
    return (
        f"<b>💸 <code>{credit.number}\n</code></b>"
        f"🏦 {credit.name} {credit.status}\n"
        f"📊 Ставка: {credit.rate}% | Срок: {credit.period} мес.\n"
        f"💰 Ежемесячный платёж: {credit.month_payment}\n"
        f"💼 Остаток: {credit.amount} {currency.get(credit.currency_number)[-1]}"
    )
