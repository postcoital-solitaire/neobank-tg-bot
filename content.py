
from models.models import Individual, Card


BLOCK_RESONES = {
    0: "115 ФЗ",
}
class Commands:
    help = ["/start", "/help"]
    profile = ["/profile", "профиль"]

class IndividualText:
    @staticmethod
    def get_registration_text(individual: Individual) -> str:
        fullname_status = f"{individual.fullname}" if individual.fullname else "🚫 ФИО"
        birthdate_status = f"{individual.birthdate}" if individual.birthdate else "🚫 Дата рождения"
        number_status = f"{individual.series} {individual.number}" if individual.series or individual.number else "🚫 Серия и номер паспорта"
        passport_photo_status = f"✅ Лицевое фото паспорта" if individual.docx_first_page else "🚫 Лицевое фото паспорта"
        registration_photo_status = f"✅ Фото прописки" if individual.docx_second_page else "🚫 Фото прописки"

        return (f"<b>{fullname_status}</b>\n"
                f"<code>{birthdate_status}</code>\n"
                f"<code>{number_status}</code>\n"
                f"<i>{passport_photo_status}</i>\n"
                f"<i>{registration_photo_status}</i>\n")

class WorkerText:
    @staticmethod
    def greet_text(individual: Individual):
        return (f"Здравствуйте, для начала работы пройдите регистрацию!\n"
                f"{IndividualText.get_registration_text(individual)}"
                f"Отпрвавьте лицевую сторону паспорта!\n")

    REG_END = "Регистрация пройдена, теперь вступай в команду по айдищнику и добавляй карты"
    PROFILE = "ПРОФИЛЬ"

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
