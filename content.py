currency = {
    643: ("Рубль", "RUB"),
    840: ("Доллар США", "USD"),
    978: ("Евро", "EUR"),
    156: ("Юань", "CNY"),
    949: ("Турецких лир", "TRY")
}

def get_currency_symbol(currency_code: int) -> str:
    symbols = {
        643: "₽",
        840: "$",
        978: "€"
    }
    return symbols.get(currency_code, "")

from typing import Dict, TypedDict

class DepositOption(TypedDict):
    id: str
    rate: float
    period: int

DEPOSIT_OPTIONS: Dict[str, Dict[str, DepositOption]] = {
    "Идеальный старт": {
        "3 месяца: 7%": {"id": "3422b448-2460-4fd2-9183-8000de6f8331", "rate": 7, "period": 3},
        "6 месяцев: 7.5%": {"id": "3422b448-2460-4fd2-9183-8000de6f8332", "rate": 7.5, "period": 6},
        "9 месяцев: 7.7%": {"id": "3422b448-2460-4fd2-9183-8000de6f8333", "rate": 7.7, "period": 9},
        "12 месяцев: 8%": {"id": "3422b448-2460-4fd2-9183-8000de6f8334", "rate": 8, "period": 12},
        "1 месяц: 1%": {"id": "74885c09-1030-dbda-b310-6921695bfdae", "rate": 1, "period": 1},
        "1 месяц: 99%": {"id": "41050565-fdf1-4424-8549-275eb74fce26", "rate": 99, "period": 1}
    },
    "Отличное начало": {
        "3 месяца: 8%": {"id": "3422b448-2460-4fd2-9183-8000de6f8335", "rate": 8, "period": 3},
        "5 месяцев: 8.5%": {"id": "3422b448-2460-4fd2-9183-8000de6f8336", "rate": 8.5, "period": 5},
        "18 месяцев: 9%": {"id": "3422b448-2460-4fd2-9183-8000de6f8337", "rate": 9, "period": 18},
        "1 месяц: 99.9%": {"id": "ac6f68af-8d67-422e-8e46-302680a357a6", "rate": 99.9, "period": 1},
        "12 месяцев: 0.1%": {"id": "7418c006-6a69-4650-a52c-0156a476a382", "rate": 0.1, "period": 12}
    },
    "Блестящий запуск": {
        "12 месяц: 9%": {"id": "3422b448-2460-4fd2-9183-8000de6f8338", "rate": 9, "period": 12},
        "24 месяца: 9.5%": {"id": "3422b448-2460-4fd2-9183-8000de6f8339", "rate": 9.5, "period": 24}
    },
    "Турецкий старт": {
        "1 месяца: 50%": {"id": "5358e35c-87aa-41dd-8470-86848b4e81ba", "rate": 50, "period": 1}
    }
}
from aiogram.types import Message

async def send_long_message(chat_id, text: str, bot, reply_markup=None, parse_mode="HTML"):
    chunk_size = 4096
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        await bot.send_message(chat_id, chunk, reply_markup=reply_markup if i + chunk_size >= len(text) else None, parse_mode=parse_mode)

BLOCK_RESONES = {
    0: "115 ФЗ",
}
class Commands:
    help = ["/start", "/help"]
    profile = ["/profile", "профиль"]

class Text:
    IN_DEVELOPMENT = "🛠 В разработке ... 🛠"

    AGREE = "Подтверждаю"

    ENTER_FIO = "Пожалуйста, введите ваше ФИО."
    FIO_ERROR = "ФИО неккоректное. Пожалуйста, введите его правильно."

    MAIL_ERROR = "Почта неккоректна. Пожалуйста, введите её правильно."

    ENTER_PHONE = "Пожалуйста, укажите ваш номер телефона в формате +79999999999"
    PHONE_ERROR = "Телефон неккоректен. Пожалуйста, введите его правильно."

    WAIT_FOR_CARD = ("Отправьте номер карты\n"
                     "Например <code>2200700771078358</code>\n\n")

    PASSPORT_ERROR = "🆘 Ошибка определения паспорта! Cфотографируйте четче."
    FULLNAME_ERROR = "🆘 Ошибка изменения! Придерживайтесь формата."

    PROFILE = "ℹ️ Личный кабинет"
    PAYMENT = "💳 Выплаты"
    HELP = "💬 Помощь"
    VIEW_LEADS = "📊 Ссылка на ПП"
    UPLOAD_LEADS = "📝 Выгрузить Лидов"

    EDIT = "📝 Редактировать"

    NOTIFICATION = "🔔 Уведомления"

    CANCEL = "✋ Отмена"

    BY_FILE = "📄 Файлом"
    JOIN_TEAM = "💬 Вступить в тиму"

    SUPPORT = "🆘 Поддержка"
    INFO = "📄 Информация"
    OUR_CHANEL = "🔔 Наш канал"

    PAYMENT_TEXT = "Текущая карта:\n💳: <code>{payment_account}</code>"

    REQ_REQ = "💳 Реквизиты"

    BACK = "⬅️ Пред."
    NEXT = "➡️ След."

    RETURN = "⬅️ Назад"

    BACK_TO_MENU = "Вернутсья в меню"

    SHORT_LINK = "🔗 Сократить ссылку"
    UTM_SOURCE = "📌 UTM Установить"

    DOWN = "⬇️ Опустить сообщение"

    ACTIVATE = "✅ Актив."
    DEACTIVATE = "🚫 Деактив."

    SEARCH_USERS = "🔍 Поиск пользователя"


    UPDATE_REQ = "♻️ Обновить реквизиты"

    SUCCESS = "✅ УСПЕШНО"
    FAILED = "🚫 Что-то пошло не так, обратитесь в тех.поддержку @eshhka_support"

    OK = "✅ ОК"
    OWN_DATES = "📝Свое"


def get_bank(card_number):
    bin_prefix = str(card_number)[:6]
    if bin_prefix.startswith(('4276', '4279', '2202')):
        bank = '🟩 Sberbank'
    elif bin_prefix.startswith(('5100', '5123', '5125')):
        bank = '🟨 Raiffeisen'
    elif bin_prefix.startswith(('5612', '5613')):
        bank = '🟦 Ozon'
    else:
        bank = 'Unknown'
    return bank
