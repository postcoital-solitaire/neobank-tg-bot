from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message

from content import get_currency_symbol, DEPOSIT_OPTIONS
from filters.filter import IsTextFilter
from main import api
from models.models import OpenStates
from content import CURRENCY

router = Router()
router.message.filter(IsTextFilter())

@router.callback_query(F.data.startswith("open_"))
async def handle_open_action(call: CallbackQuery, state: FSMContext):
    _, product_type = call.data.split("_", 1)

    token = api.try_get_token(call.message.chat.id)
    if not token:
        await call.answer("❌ Требуется авторизация")
        return

    if product_type == "account":
        await handle_open_account(call, state)
    elif product_type == "deposit":
        await handle_open_deposit(call, state)
    elif product_type == "credit":
        await handle_open_credit(call, state)


async def handle_open_account(call: CallbackQuery, state: FSMContext):
    """Обработка открытия нового счета"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{currency[0]} ({currency[1]})", callback_data=f"op_acc_cur:{code}")]
        for code, currency in CURRENCY.items()
    ])

    await call.message.edit_text(
        "💳 Выберите валюту для нового счета:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("op_acc_cur:"))
async def handle_account_currency_selection(call: CallbackQuery, state: FSMContext):
    """Обработка выбора валюты для счета"""
    currency_code = int(call.data.split(":")[1])
    await state.update_data(currency=currency_code)

    await call.message.edit_text(
        f"💳 Введите сумму для открытия счета в {get_currency_symbol(currency_code)}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel:account")]
        ])
    )
    await call.answer()
    await state.set_state(OpenStates.waiting_for_account_amount)


@router.message(OpenStates.waiting_for_account_amount)
async def handle_account_amount_input(message: Message, state: FSMContext):
    """Обработка ввода суммы для открытия счета"""
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверная сумма. Введите положительное число:")
        return

    data = await state.get_data()
    currency_code = data["currency"]

    token = api.try_get_token(message.chat.id)
    if not token:
        await message.answer("❌ Требуется авторизация")
        return

    try:
        account = await api.open_account(token, currency_code, amount)
        await message.answer(
            f"✅ Счет успешно открыт!\n"
            f"Номер: <code>{account.account_number}</code>\n"
            f"Сумма: {amount:.2f} {get_currency_symbol(currency_code)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← К списку счетов", callback_data="list:account")]
                ]
            ),
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка при открытии счета: {str(e)}")


async def handle_open_deposit(call: CallbackQuery, state: FSMContext):
    """Обработка открытия нового вклада"""
    token = api.try_get_token(call.message.chat.id)
    if not token:
        await call.answer("❌ Требуется авторизация")
        return

    accounts = await api.get_accounts(token)
    rub_accounts = [acc for acc in accounts if acc.book == 0 and acc.status == "ACTIVE" and acc.currency_number == 643]

    if not rub_accounts:
        await call.message.edit_text(
            "❌ У вас нет активных рублевых счетов для открытия вклада",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="list:deposit")]
            ]
            )
        )
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{acc.account_number} ({acc.amount:.2f} {get_currency_symbol(acc.currency_number)})",
            callback_data=f"select_deposit_account:{acc.id}"
        )] for acc in rub_accounts
    ])

    await call.message.edit_text(
        "💰 Выберите счет для открытия вклада:",
        reply_markup=keyboard
    )
    await state.set_state(OpenStates.waiting_for_deposit_account)


@router.callback_query(F.data.startswith("select_deposit_account:"), OpenStates.waiting_for_deposit_account)
async def handle_deposit_account_selection(call: CallbackQuery, state: FSMContext):
    """Обработка выбора счета для вклада"""
    account_id = call.data.split(":")[1]
    await state.update_data(account_id=account_id)

    # Получаем список доступных вкладов
    deposit_options = DEPOSIT_OPTIONS

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"select_deposit_type:{name}")]
        for name in deposit_options.keys()
    ])

    await call.message.edit_text(
        "💰 Выберите тип вклада:",
        reply_markup=keyboard
    )
    await state.set_state(OpenStates.waiting_for_deposit_type)


@router.callback_query(F.data.startswith("select_deposit_type:"), OpenStates.waiting_for_deposit_type)
async def handle_deposit_type_selection(call: CallbackQuery, state: FSMContext):
    """Обработка выбора типа вклада"""
    deposit_type = call.data.split(":")[1]
    options = DEPOSIT_OPTIONS.get(deposit_type, {})

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name}",
            callback_data=f"sel_dep_opt:{deposit_type}:{name}"
        )] for name, opt in options.items()
    ])

    await call.message.edit_text(
        f"💰 Выберите вариант вклада '{deposit_type}':",
        reply_markup=keyboard
    )
    await state.set_state(OpenStates.waiting_for_deposit_option)


@router.callback_query(F.data.startswith("sel_dep_opt:"), OpenStates.waiting_for_deposit_option)
async def handle_deposit_option_selection(call: CallbackQuery, state: FSMContext):
    """Обработка выбора опции вклада"""
    _, deposit_type, option_name, percent = call.data.split(":")
    option_name = option_name + ":" + percent

    option = DEPOSIT_OPTIONS[deposit_type][option_name]

    await state.update_data(
        deposit_type=deposit_type,
        option_name=option_name,
        option=option
    )

    await call.message.edit_text(
        f"💰 Введите сумму для открытия вклада\n"
        f"<b>'{deposit_type} - {option_name}'</b>:\n"
        f"<i>Минимальная сумма: {30000}₽ </i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel:deposit")]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(OpenStates.waiting_for_deposit_amount)


@router.message(OpenStates.waiting_for_deposit_amount)
async def handle_deposit_amount_input(message: Message, state: FSMContext):
    """Обработка ввода суммы для вклада"""
    try:
        amount = float(message.text)
        data = await state.get_data()
        min_amount = data["option"].get("min_amount", 0)

        if amount < min_amount:
            await message.answer(f"❌ Минимальная сумма для этого вклада: {min_amount:.2f} ₽")
            return
    except ValueError:
        await message.answer("❌ Неверная сумма. Введите положительное число:")
        return

    token = api.try_get_token(message.chat.id)
    if not token:
        await message.answer("❌ Требуется авторизация")
        return

    data = await state.get_data()

    try:
        deposit = await api.open_deposit_with_option(
            token=token,
            account_id=data["account_id"],
            product_name=data["deposit_type"],
            option_name=data["option_name"],
            amount=amount,
            auto_prolongation=True
        )

        await message.answer(
            f"✅ Вклад успешно открыт!\n"
            f"Номер: {deposit.number}\n"
            f"Сумма: {amount:.2f} ₽\n"
            f"Ставка: {deposit.rate}%\n"
            f"Срок: {deposit.period} мес.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← К списку вкладов", callback_data="list:deposit")]
            ])
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка при открытии вклада: {str(e)}")


async def handle_open_credit(call: CallbackQuery, state: FSMContext):
    """Обработка открытия нового кредита"""
    token = api.try_get_token(call.message.chat.id)
    if not token:
        await call.answer("❌ Требуется авторизация")
        return

    # Получаем список кредитных продуктов
    try:
        products = await api.get_credit_products(token)
        if not products:
            await call.message.edit_text(
                "❌ Нет доступных кредитных продуктов",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="← Назад", callback_data="list:credit")]
                ])
            )
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=prod["name"], callback_data=f"select_credit_product:{prod['id']}")]
            for prod in products
        ])

        await call.message.edit_text(
            "💵 Выберите кредитный продукт:",
            reply_markup=keyboard
        )
        await state.set_state(OpenStates.waiting_for_credit_product)
    except Exception as e:
        await call.message.edit_text(f"❌ Ошибка при загрузке кредитных продуктов: {str(e)}")


@router.callback_query(F.data.startswith("select_credit_product:"), OpenStates.waiting_for_credit_product)
async def handle_credit_product_selection(call: CallbackQuery, state: FSMContext):
    """Обработка выбора кредитного продукта"""
    product_id = call.data.split(":")[1]
    await state.update_data(product_id=product_id)

    await call.message.edit_text(
        "💵 Введите сумму кредита:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel:credit")]
        ])
    )
    await state.set_state(OpenStates.waiting_for_credit_amount)


@router.message(OpenStates.waiting_for_credit_amount)
async def handle_credit_amount_input(message: Message, state: FSMContext):
    """Обработка ввода суммы кредита"""
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверная сумма. Введите положительное число:")
        return

    await state.update_data(amount=amount)

    await message.answer(
        "💵 Введите срок кредита (в месяцах):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel:credit")]
        ])
    )
    await state.set_state(OpenStates.waiting_for_credit_period)


@router.message(OpenStates.waiting_for_credit_period)
async def handle_credit_period_input(message: Message, state: FSMContext):
    """Обработка ввода срока кредита"""
    try:
        period = int(message.text)
        if period <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный срок. Введите целое число месяцев:")
        return

    token = api.try_get_token(message.chat.id)
    if not token:
        await message.answer("❌ Требуется авторизация")
        return

    data = await state.get_data()

    try:
        # Получаем расчет кредита
        calculation = await api.calculate_credit_offer(
            token=token,
            product_id=data["product_id"],
            amount=data["amount"],
            period=period
        )

        # Получаем список счетов для выбора
        accounts = await api.get_accounts(token)
        rub_accounts = [acc for acc in accounts if acc.currency_number == 643 and acc.status == "ACTIVE"]

        if not rub_accounts:
            await message.answer(
                "❌ У вас нет активных рублевых счетов для получения кредита",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="← Назад", callback_data="list:credit")]]
                )
            )
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{acc.account_number}",
                callback_data=f"select_credit_account:{acc.id}"
            )] for acc in rub_accounts
        ])

        await state.update_data(
            period=period,
            calculation=calculation
        )

        await message.answer(
            f"💵 Условия кредита:\n"
            f"Сумма: {data['amount']:.2f} ₽\n"
            f"Срок: {period} мес.\n"
            f"Ставка: {calculation['rate']}%\n"
            f"Ежемесячный платеж: {calculation['monthPayment']:.2f} ₽\n\n"
            "Выберите счет для зачисления средств:",
            reply_markup=keyboard
        )
        await state.set_state(OpenStates.waiting_for_credit_account)
    except Exception as e:
        await message.answer(f"❌ Ошибка при расчете кредита: {str(e)}")


@router.callback_query(F.data.startswith("select_credit_account:"), OpenStates.waiting_for_credit_account)
async def handle_credit_account_selection(call: CallbackQuery, state: FSMContext):
    """Обработка выбора счета для кредита"""
    account_id = call.data.split(":")[1]

    token = api.try_get_token(call.message.chat.id)
    if not token:
        await call.answer("❌ Требуется авторизация")
        return

    data = await state.get_data()

    try:
        credit = await api.open_credit(
            token=token,
            account_id=account_id,
            product_id=data["product_id"],
            amount=data["amount"],
            period=data["period"]
        )

        await call.message.edit_text(
            f"✅ Кредит успешно оформлен!\n"
            f"Номер: {credit.number}\n"
            f"Сумма: {data['amount']:.2f} ₽\n"
            f"Срок: {data['period']} мес.\n"
            f"Ставка: {data['calculation']['rate']}%\n"
            f"Ежемесячный платеж: {data['calculation']['monthPayment']:.2f} ₽",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← К списку кредитов", callback_data="list:credit")]]
            )
        )
        await state.clear()
    except Exception as e:
        await call.message.edit_text(f"❌ Ошибка при оформлении кредита: {str(e)}")

