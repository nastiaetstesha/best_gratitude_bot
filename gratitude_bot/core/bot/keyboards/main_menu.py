# gratitude_bot/core/bot/keyboards/main_menu.py

from telegram import ReplyKeyboardMarkup

BACK_BUTTON = "⬅️ Назад в меню"

# --- History buttons ---
HISTORY_BY_DATE_BUTTON = "Посмотреть ответы за дату"
HISTORY_PROGRESS_BUTTON = "Посмотреть прогресс"
HISTORY_SEARCH_BUTTON = "Поиск по записям"

# --- Statistics buttons ---
STATS_GENERAL_BUTTON = "Общая статистика"
STATS_CHART_BUTTON = "График заполнений"
STATS_TOPICS_BUTTON = "Частые темы благодарности"
STATS_WEEKDAYS_BUTTON = "Статистика по дням недели"

# --- Settings buttons (вариант с тумблерами “вкл/выкл” в одном тексте) ---
SET_TZ_BUTTON = "Часовой пояс"
SET_MORNING_TIME_BUTTON = "Время утреннего напоминания"
SET_EVENING_TIME_BUTTON = "Время вечернего напоминания"
SET_WEEK_START_BUTTON = "День начала недели"

TOGGLE_MORNING_BUTTON = "Утренние напоминания: вкл/выкл"
TOGGLE_EVENING_BUTTON = "Вечерние напоминания: вкл/выкл"
TOGGLE_MISSED_BUTTON = "Уведомления о пропусках: вкл/выкл"


def get_main_menu_keyboard():
    buttons = [
        ["Сегодня", "Утро"],
        ["Вечер", "Неделя"],
        ["История"],
        ["Статистика", "Настройки"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)


def get_cancel_keyboard():
    return ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True, one_time_keyboard=True)


def get_today_menu_keyboard():
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
    return ReplyKeyboardMarkup(
        [
            [STATS_GENERAL_BUTTON, STATS_CHART_BUTTON],
            [STATS_TOPICS_BUTTON],
            [STATS_WEEKDAYS_BUTTON],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_settings_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [SET_TZ_BUTTON],
            [SET_MORNING_TIME_BUTTON, SET_EVENING_TIME_BUTTON],
            [TOGGLE_MORNING_BUTTON, TOGGLE_EVENING_BUTTON],
            [TOGGLE_MISSED_BUTTON],
            [SET_WEEK_START_BUTTON],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_schedule_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Спасти стрик"],
            ["Напомни позже", "Сегодня пропускаю"],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
