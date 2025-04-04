import os
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import content
from api.rupassported import catching
from content import IndividualText
from filters.filter import *
from keybords.worker import registration
from main import dm
from models.models import DefaultActions, Action, Individual, Card
from states.state import States

router = Router()

downloads_dir = 'cache'

@router.message(
    WithFullIndividual(False),
    TypicalFilter(for_replace=content.Commands.help)
)
async def start_menu(message: Message, state: FSMContext):
    ind = Individual()

    worker = Worker(telegram_id=message.from_user.id,
                    is_active=True,)

    if await dm.execute_query(worker.get_one):
        ind.id = worker.individual_id
        await dm.execute_query(ind.get_one)
        if ind.docx_first_page is not None:
            await message.answer(
                text=IndividualText.get_registration_text(ind),
                parse_mode="HTML",
                reply_markup=registration._buttons(ind.number)
            )
            await state.update_data(docx=ind.docx_first_page)
            await state.set_state(States.waiting_for_second_photo)
            return

    worker.join_time = datetime.now()
    worker.username = message.from_user.username

    await dm.execute_query(worker.add)

    msg = await message.answer(content.WorkerText.greet_text(ind),
                               parse_mode="HTML")

    await state.set_state(States.waiting_for_photo)
    await state.update_data(msg_id=msg.message_id)


"""ХУЕТЕНЬ"""
@router.message(
    States.waiting_for_photo,
    WithPhoto()
)
async def waiting_for_photo(message: Message, bot: Bot, state: FSMContext):
    file_id = message.photo[-1].file_id

    if "msg_id" not in (await state.get_data()):
        card_number = (await state.get_data())["card_number"]

        card = Card(card_number=card_number)
        await dm.execute_query(card.get_one)

        temp_path = await download_picture(bot, file_id)
        ind = catching(temp_path)
        ind.docx_first_page = temp_path

        await dm.execute_query(ind.add)
        await dm.execute_query(ind.get_one)

        card.individual_id = ind.id
        await dm.execute_query(card.update, where_field="card_number")
        await state.update_data(docx=temp_path)

        msg = await bot.send_message(
            chat_id=message.chat.id,
            text=IndividualText.get_registration_text(ind),
            parse_mode="HTML",
            reply_markup=registration._buttons(ind.number)
        )

        await state.update_data(msg_id=msg.message_id)
        await state.update_data(card_add=True)
        await state.set_state(States.waiting_for_second_photo)
        return
    msg_id = (await state.get_data())["msg_id"]

    temp_path = await download_picture(bot, file_id)

    ind = catching(temp_path)

    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=msg_id)

    ind.docx_first_page = temp_path

    await dm.execute_query(ind.add)
    await dm.execute_query(ind.get_one)

    worker = Worker(telegram_id=message.from_user.id,
                    individual_id=ind.id)
    await dm.execute_query(worker.update, where_field="telegram_id")

    await state.update_data(docx=temp_path)

    msg = await message.answer(
        text=IndividualText.get_registration_text(ind),
        message_id=msg_id,
        parse_mode="HTML",
        reply_markup=registration._buttons(ind.number)
    )

    await state.update_data(msg_id=msg.message_id)
    await state.set_state(States.waiting_for_second_photo)


@router.message(
    States.waiting_for_second_photo,
    WithPhoto()
)
async def waiting_for_second_photo(message: Message, bot: Bot, state: FSMContext):
    second_file_id = message.photo[-1].file_id
    temp_path = await download_picture(bot, second_file_id)

    if "msg_id" in (await state.get_data()):
        msg_id = (await state.get_data())["msg_id"]
        await bot.delete_message(chat_id=message.from_user.id,
                                 message_id=msg_id)

    docx_first_page = (await state.get_data())["docx"]

    ind = Individual(docx_first_page=docx_first_page)

    await dm.execute_query(ind.get_one)
    ind.docx_second_page = temp_path
    await dm.execute_query(ind.update)

    if (await state.get_data())["card_add"]:
        await message.answer(
            text=IndividualText.get_registration_text(ind),
            parse_mode="HTML",
            reply_markup=registration._buttons_end(ind.number, True)
        )

    await message.answer(
        text=IndividualText.get_registration_text(ind),
        parse_mode="HTML",
        reply_markup=registration._buttons_end(ind.number)
    )

    await state.clear()


@router.message(
    States.waiting_for_fullname_edit,
)
async def waiting_for_fullname_edit(message: Message, state: FSMContext, bot: Bot):
    docx_first_page = (await state.get_data())["docx"]
    msg_id = (await state.get_data())["msg_id"]

    ind = Individual(docx_first_page=docx_first_page)
    try:
        ind.fullname = message.text.strip().upper()
        await dm.execute_query(ind.update)
        await dm.execute_query(ind.get_one)
    except Exception:
        await bot.send_message(chat_id=message.from_user.id,
                               text=content.Text.FULLNAME_ERROR)
        return

    text = "-->" + IndividualText.get_registration_text(ind)

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=msg_id,
        text=text + "\n<b>ВВЕДИТЕ КОРРЕКТНЫЙ ВАРИАНТ СТРОКИ</b>",
        parse_mode="HTML",
        reply_markup=registration._buttons_check_fullname(ind.number)
    )
    await bot.delete_message(message_id=message.message_id,
                             chat_id=message.from_user.id)


@router.message(
    States.waiting_for_birthdate_edit,
)
async def waiting_for_birth_edit(message: Message, state: FSMContext, bot: Bot):
    docx_first_page = (await state.get_data())["docx"]
    msg_id = (await state.get_data())["msg_id"]

    ind = Individual(docx_first_page=docx_first_page)

    ind.birthdate = message.text.strip()
    await dm.execute_query(ind.update)
    await dm.execute_query(ind.get_one)

    text = IndividualText.get_registration_text(ind).split("\n")
    text = "\n".join(text[:1]) + "\n-->" + "\n".join(text[1:])

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=msg_id,
        text=text + "<b>ВВЕДИТЕ КОРРЕКТНЫЙ ВАРИАНТ СТРОКИ</b>",
        parse_mode="HTML",
        reply_markup=registration._buttons_check_birthdate(ind.number)
    )
    await bot.delete_message(message_id=message.message_id,
                             chat_id=message.from_user.id)


@router.message(
    States.waiting_for_numbers_edit,
)
async def waiting_for_numbers_edit(message: Message, state: FSMContext, bot: Bot):
    try:
        docx_first_page = (await state.get_data())["docx"]
    except Exception:
        return

    msg_id = (await state.get_data())["msg_id"]

    ind = Individual(docx_first_page=docx_first_page)

    numbers = message.text.strip().replace(" ", "")
    if len(numbers) != 10:
        return

    ind.series = numbers[:4]
    ind.number = numbers[4:]

    await dm.execute_query(ind.update)
    await dm.execute_query(ind.get_one)

    text = IndividualText.get_registration_text(ind).split("\n")
    text = "\n".join(text[:2]) + "\n-->" + "\n".join(text[2:])

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=msg_id,
        text=text + "<b>ВВЕДИТЕ КОРРЕКТНЫЙ ВАРИАНТ СТРОКИ</b>",
        parse_mode="HTML",
        reply_markup=registration._buttons_check_numbers(ind.number)
    )

    await bot.delete_message(message_id=message.message_id,
                             chat_id=message.from_user.id)


@router.callback_query(
    DefaultActions.filter(F.action == Action.cancel))
async def back_to_profile(call_q: CallbackQuery, state: FSMContext):
    ind = Individual(number=call_q.data.split(":")[2])

    await dm.execute_query(ind.get_one)
    await dm.execute_query(Worker(individual_id=ind.id).delete)
    await dm.execute_query(ind.delete)

    ind = Individual()
    await call_q.message.edit_text(
        content.WorkerText.greet_text(ind),
        parse_mode="HTML"
    )
    await call_q.answer()
    await state.set_state(States.waiting_for_photo)


@router.callback_query(
    DefaultActions.filter(F.action == Action.edit))
async def edit_fullname(call_q: CallbackQuery, state: FSMContext):
    ind = Individual(number=call_q.data.split(":")[2])

    await dm.execute_query(ind.get_one)

    text = "-->" + IndividualText.get_registration_text(ind)

    await call_q.message.edit_text(
        text=text + "<b>ВВЕДИТЕ КОРРЕКТНЫЙ ВАРИАНТ СТРОКИ</b>",
        parse_mode="HTML",
        reply_markup=registration._buttons_check_fullname(ind.number)
    )
    await call_q.answer()
    await state.set_state(States.waiting_for_fullname_edit)


@router.callback_query(
    DefaultActions.filter(F.action == Action.edit_birthdate))
async def edit_birthdate(call_q: CallbackQuery, state: FSMContext):
    ind = Individual(number=call_q.data.split(":")[2])

    await dm.execute_query(ind.get_one)

    text = IndividualText.get_registration_text(ind).split("\n")
    text = "\n".join(text[:1]) + "\n-->" + "\n".join(text[1:])

    await call_q.message.edit_text(
        text=text + "<b>ВВЕДИТЕ КОРРЕКТНЫЙ ВАРИАНТ СТРОКИ</b>",
        parse_mode="HTML",
        reply_markup=registration._buttons_check_birthdate(ind.number)
    )
    await call_q.answer()
    await state.set_state(States.waiting_for_birthdate_edit)


@router.callback_query(
    DefaultActions.filter(F.action == Action.edit_numbers))
async def edit_numbers(call_q: CallbackQuery, state: FSMContext):
    ind = Individual(number=call_q.data.split(":")[2])

    await dm.execute_query(ind.get_one)

    text = IndividualText.get_registration_text(ind).split("\n")
    text = "\n".join(text[:2]) + "\n-->" + "\n".join(text[2:])

    await call_q.message.edit_text(
        text=text + "<b>ВВЕДИТЕ КОРРЕКТНЫЙ ВАРИАНТ СТРОКИ</b>",
        parse_mode="HTML",
        reply_markup=registration._buttons_check_numbers(ind.number)
    )
    await call_q.answer()
    await state.set_state(States.waiting_for_numbers_edit)


@router.callback_query(
    DefaultActions.filter(F.action == Action.stop))
async def stop(call_q: CallbackQuery, state: FSMContext):
    ind = Individual(number=call_q.data.split(":")[2])

    await dm.execute_query(ind.get_one)

    msg = await call_q.message.edit_text(
        text=IndividualText.get_registration_text(ind),
        parse_mode="HTML",
        reply_markup=registration._buttons(ind.number)
    )

    await call_q.answer()
    await state.set_state(States.waiting_for_second_photo)


async def download_picture(bot, file_id):
    file = await bot.get_file(file_id)
    file_path = file.file_path
    os.makedirs(downloads_dir, exist_ok=True)
    temp_path = os.path.join(downloads_dir, f'{file_id}.jpg')
    await bot.download_file(file_path, destination=temp_path)
    return temp_path
