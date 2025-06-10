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
