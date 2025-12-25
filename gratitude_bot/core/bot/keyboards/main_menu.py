
from telegram import ReplyKeyboardMarkup

BACK_BUTTON = "⬅️ Назад в меню"

# Кнопки истории (если ты их импортируешь в bot.py)
HISTORY_BY_DATE_BUTTON = "Посмотреть ответы за дату"
HISTORY_PROGRESS_BUTTON = "Посмотреть прогресс"
HISTORY_SEARCH_BUTTON = "Поиск по записям"


def get_main_menu_keyboard():
    """
    Основное меню
    """
    buttons = [
        ["Сегодня", "Утро"],
        ["Вечер", "Неделя"],
        ["История"],
        ["Статистика", "Настройки"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)


def get_cancel_keyboard():
    """
    Клавиатура с единственной кнопкой "Назад в меню"
    (используется внутри диалогов/опросников)
    """
    return ReplyKeyboardMarkup(
        [[BACK_BUTTON]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_today_menu_keyboard():
    """
    Меню "Сегодня"
    """
    return ReplyKeyboardMarkup(
        [
            ["Заполнить утро", "Заполнить вечер"],
            ["Посмотреть сегодняшние ответы", "Пропустить сегодня"],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_morning_completed_keyboard():
    """
    Когда утро уже заполнено: даём посмотреть или перезаполнить
    """
    return ReplyKeyboardMarkup(
        [
            ["Посмотреть сегодняшние ответы"],
            ["Заполнить утро заново"],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_week_menu_keyboard():
    """
    Меню "Неделя"
    """
    return ReplyKeyboardMarkup(
        [
            ["Заполнить неделю"],
            ["Посмотреть недельные ответы"],
            ["Задание недели"],
            ["Заполнить неделю заново"],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_history_menu_keyboard():
    """
    Меню "История"
    """
    return ReplyKeyboardMarkup(
        [
            [HISTORY_BY_DATE_BUTTON],
            [HISTORY_PROGRESS_BUTTON, HISTORY_SEARCH_BUTTON],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_statistics_menu_keyboard():
    """
    Меню "Статистика"
    (пока заглушки — ты можешь позже подключить обработчики)
    """
    return ReplyKeyboardMarkup(
        [
            ["Общая статистика", "График заполнений", "Частые темы благодарности"],
            ["Статистика по дням недели"],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_settings_menu_keyboard():
    """
    Меню "Настройки"
    (пока заглушки — ты можешь позже подключить обработчики)
    """
    return ReplyKeyboardMarkup(
        [
            ["Изменить время утреннего напоминания", "Изменить время вечернего напоминания"],
            ["Изменить день начала недели", "Уведомления о пропусках"],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_schedule_keyboard():
    """
    Клавиатура для "напоминаний/спасения стрика"
    """
    return ReplyKeyboardMarkup(
        [
            ["Спасти стрик"],
            ["Напомни позже", "Сегодня пропускаю"],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
