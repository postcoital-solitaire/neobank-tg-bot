from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
import re

from rupasportread import catching

import content
from filters.filter import *
from handlers.worker.registration_handler import download_picture
from keybords.worker import main, registration
from models.models import DefaultActions, Action, Individual, Card
from states.state import States

router = Router()

router.message.filter(
    WithFullIndividual(True),
    IsTextFilter(),
)

@router.message(
    TypicalFilter(for_replace=content.Commands.help)
)
async def start_menu(message: Message):
    cards = Card(worker_id=message.from_user.id)
    if len(await dm.execute_query(cards.get_many)) > 0:
        await message.answer(
            text=content.WorkerText.PROFILE,
            parse_mode="HTML",
            reply_markup=main._buttons_middle()
        )
        return

    await message.answer(
        text=content.WorkerText.PROFILE,
        parse_mode="HTML",
        reply_markup=main._buttons_beginner()
    )

@router.callback_query(
    DefaultActions.filter(F.action == Action.verificate))
async def verificate(call_q: CallbackQuery, state: FSMContext):
    await state.clear()

    ind = Individual(number=call_q.data.split(":")[2])
    await dm.execute_query(ind.get_one)

    await call_q.message.edit_text(
        text=content.WorkerText.REG_END,
        parse_mode="HTML",
        reply_markup=main._buttons_beginner()
    )


@router.callback_query(
    DefaultActions.filter(F.action == Action.add_card))
async def add_card(call_q: CallbackQuery, state: FSMContext):
    card = Card(worker_id=call_q.from_user.id,
                card_status=0,
                is_valid=True,
                add_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    await dm.execute_query(card.add)

    await call_q.message.answer(
        text=content.CardText.CARD_NUMBER,
        parse_mode="HTML"
    )

    await state.set_state(States.waiting_for_card_number)


@router.callback_query(
    DefaultActions.filter(F.action == Action.my_cards))
async def my_cards(call_q: CallbackQuery, bot: Bot):
    cards = Card(worker_id=call_q.from_user.id)
    cards= await dm.execute_query(cards.get_many)

    await bot.send_message(
        chat_id=call_q.from_user.id,
        text=content.CardText.CARD_LIST_TEXT,
        parse_mode="HTML",
        reply_markup=main._buttons_cards_list(cards)
    )

@router.callback_query(
    DefaultActions.filter(F.action == Action.del_card))
async def del_card(call_q: CallbackQuery, bot: Bot):
    card = Card(card_number=call_q.data.split(":")[2])
    await dm.execute_query(card.delete)

    await bot.delete_message(chat_id=call_q.from_user.id,
                             message_id=call_q.message.message_id)

    await my_cards(call_q, bot)

@router.callback_query(
    DefaultActions.filter(F.action == Action.info_card))
async def info_card(call_q: CallbackQuery, bot: Bot):
    card = Card(card_number=call_q.data.split(":")[2])
    await dm.execute_query(card.get_one)

    text = await content.CardText.get_add_text(card)

    if card.individual_id is None:
        await bot.send_message(
            chat_id=call_q.from_user.id,
            text=text,
            parse_mode="HTML",
            reply_markup=main._buttons_need_individual(str(card.card_number))
        )
        return

    await bot.send_message(
        chat_id=call_q.from_user.id,
        text=text,
        parse_mode="HTML",
        reply_markup=main._buttons_back_to_profile()
    )

@router.callback_query(
    DefaultActions.filter(F.action == Action.add_ind_card))
async def add_ind_card(call_q: CallbackQuery, state: FSMContext):
    card = Card(card_number=call_q.data.split(":")[2])
    await dm.execute_query(card.get_one)
    await state.update_data(card_number=card.card_number)

    await call_q.message.answer(
        text=content.IndividualText.get_registration_text(Individual()),
        parse_mode="HTML"
    )
    await state.set_state(States.waiting_for_photo)

@router.message(
    States.waiting_for_photo,
    WithPhoto()
)
async def waiting_for_photo2(message: Message, bot: Bot, state: FSMContext):
    file_id = message.photo[-1].file_id
    card_number = (await state.get_data())["card_number"]

    card = Card(card_number=card_number)
    await dm.execute_query(card.get_one)

    temp_path = await download_picture(bot, file_id)
    ind = catching(temp_path)
    ind.docx_first_page = temp_path

    await dm.execute_query(ind.add)
    await dm.execute_query(ind.get_one)

    card.individual_id=ind.id
    await dm.execute_query(card.update, where_field="card_number")
    await state.update_data(docx=temp_path)

    msg = await message.answer(
        text=(await content.CardText.get_add_text(card)),
        parse_mode="HTML",
        reply_markup=registration._buttons(ind.number)
    )

    await state.update_data(msg_id=msg.message_id)
    await state.set_state(States.waiting_for_second_photo)


@router.callback_query(
    DefaultActions.filter(F.action == Action.back_to_profile))
async def back_to_profile(call_q: CallbackQuery, bot: Bot):
    await call_q.message.edit_text(
        text=content.WorkerText.PROFILE,
        parse_mode="HTML",
        reply_markup=main._buttons_middle()
    )
    await bot.delete_message(chat_id=call_q.from_user.id,
                             message_id=call_q.message.message_id)

@router.callback_query(
    DefaultActions.filter(F.action == Action.verificate_card_ind))
async def back_to_profile(call_q: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()

    ind = Individual(number=call_q.data.split(":")[2])
    await dm.execute_query(ind.get_one)

    card = Card(individual_id=ind.id)
    await dm.execute_query(card.get_one)

    card.card_status = 1
    card.add_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    await dm.execute_query(card.update, where_field="id")

    await bot.send_message(
        chat_id=call_q.from_user.id,
        text="УВЕД АДМИНУ",
        parse_mode="HTML"
    )

    await call_q.message.edit_text(
        text=content.WorkerText.PROFILE,
        parse_mode="HTML",
        reply_markup=main._buttons_middle()
    )

@router.message(
    States.waiting_for_card_number
)
async def waiting_for_card_number(call_q: CallbackQuery, state: FSMContext):
    cards = Card(worker_id=call_q.from_user.id)
    cards = await dm.execute_query(cards.get_many)
    for card in cards:
        if card.card_number is None:
            if not validate_card(call_q.text.strip()):
                await call_q.answer(
                    text=content.CardText.CARD_VALIDATION_ERROR,
                    parse_mode="HTML"
                )
                return

            card.card_number = call_q.text.strip()
            card.add_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            await dm.execute_query(card.update, where_field="id")
            break

    await call_q.answer(
        text=content.CardText.CARD_DATE,
        parse_mode="HTML"
    )

    await state.set_state(States.waiting_for_card_date)

@router.message(
    States.waiting_for_card_date
)
async def waiting_for_card_date(call_q: CallbackQuery, state: FSMContext):
    cards = Card(worker_id=call_q.from_user.id)
    cards = await dm.execute_query(cards.get_many)

    for card in cards:
        if card.activation_date is None:
            if not validate_card_date(call_q.text.strip()):
                await call_q.answer(
                    text=content.CardText.CARD_VALIDATION_ERROR,
                    parse_mode="HTML"
                )
                return

            card.activation_date = call_q.text.strip()
            card.add_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await dm.execute_query(card.update, where_field="id")
            break

    await call_q.answer(
        text=content.CardText.CARD_CVV,
        parse_mode="HTML"
    )

    await state.set_state(States.waiting_for_card_cvv)


@router.message(
    States.waiting_for_card_cvv
)
async def waiting_for_card_cvv(call_q: CallbackQuery, state: FSMContext, bot: Bot):
    cards = Card(worker_id=call_q.from_user.id)
    cards = await dm.execute_query(cards.get_many)

    for card in cards:
        if card.cvv is None:
            if not validate_cvv(call_q.text.strip()):
                await call_q.answer(
                    text=content.CardText.CARD_VALIDATION_ERROR,
                    parse_mode="HTML"
                )
                return
            card.cvv = call_q.text.strip()
            card.add_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await dm.execute_query(card.update, where_field="id")
            break

    await state.clear()

    await my_cards(call_q, bot)


async def get_notification_count():
    pass

def luhn_check(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10 == 0


def validate_card(card_number):
    card_number = re.sub(r"[\s-]+", "", card_number)
    if not card_number.isdigit():
        return False
    if len(card_number) not in [16, 18, 19]:
        return False
    if get_bank(card_number) != 'Unknown' :
        return True
    return False

def get_bank(card_number):
    bin_prefix = card_number[:6]
    if bin_prefix.startswith(('4276', '4279', '2202')):
        bank = '🟩 Sberbank'
    elif bin_prefix.startswith(('5100', '5123', '5125')):
        bank = '🟨 Raiffeisen'
    elif bin_prefix.startswith(('5612', '5613')):
        bank = '🟦 Ozon'
    else:
        bank = 'Unknown'
    return bank


def validate_date(card_cvv):
    if not card_cvv.isdigit():
        return False
    if len(card_cvv) not in [3]:
        return False

    return True


def validate_card_date(date_str):
    if not re.match(r"^(0[1-9]|1[0-2])/([0-9]{2})$", date_str):
        return False
    try:
        exp_month, exp_year = date_str.split('/')
        exp_month = int(exp_month)
        exp_year = int('20' + exp_year)
        now = datetime.now()
        expiry_date = datetime(exp_year, exp_month, 1)
        if expiry_date < now.replace(day=1, hour=0, minute=0, second=0, microsecond=0):
            return False
    except ValueError:
        return False
    return True

def validate_cvv(card_cvv):
    if not card_cvv.isdigit():
        return False
    if len(card_cvv) not in [3]:
        return False

    return True
