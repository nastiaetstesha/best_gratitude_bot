from telegram import ReplyKeyboardMarkup


BACK_BUTTON = "⬅️ Назад в меню"

def get_main_menu_keyboard():
    """
    Основое меню
    """
    buttons = [
        ["Сегодня", "Утро"],
        ["Вечер", "Неделя"],
        ["История"],
        ["Статистика", "Настройки"],
    ]

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)


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


def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        [[BACK_BUTTON]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_today_menu_keyboard():
    """Пропустить (и спросить “почему?” — опционально)"""
    return ReplyKeyboardMarkup(
    [
        ["Заполнить утро", "Заполнить вечер"],
        ["Посмотреть сегодняшние ответы", "Пропустить сегодня"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    )

# WEEK_FILL_BUTTON = "❤️ Заполнить неделю"
# WEEK_VIEW_BUTTON = "Посмотреть недельные ответы"
# WEEK_TASK_BUTTON = "Задание недели"
# WEEK_REDO_BUTTON = "Заполнить неделю заново"

def get_week_menu_keyboard():
    """
    “Неделя”
    Задание недели
    Промежуточный итог
    Итог недели - ?
    Выбрать новую неделю (если хотите ручной старт) -? пока нет
    """
    return ReplyKeyboardMarkup(
        [
            ["Заполнить неделю", "Посмотреть недельные ответы",
             "Задание недели"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_history_menu_keyboard():
    """
    “История”
    За дату (выбор: сегодня/вчера/календарь кнопками)
    За неделю
    За месяц
    Последние 10 записей
    Поиск
    """
    return ReplyKeyboardMarkup(
       [["Посмотреть ответы за дату"],
        ["Посмотреть прогресс", "Поиск по записям"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_statistics_menu_keyboard():
    """
    “Статистика”
    Общая статистика
    Статистика по утрам
    Статистика по вечерам
    Статистика по дням недели
    ---
    Стрик
    График заполнений (просто числа по дням)
    Частые темы благодарности
    Экспорт - ?
    """
    return ReplyKeyboardMarkup(
        [
            ["Общая статистика", "График заполнений",
             "Частые темы благодарности"],
            ["Статистика по дням недели"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

def get_settings_menu_keyboard():
    """
    “Настройки”
    Изменить время утреннего напоминания
    Изменить время вечернего напоминания
    Изменить день начала недели
    Уведомления о пропусках
    """
    return ReplyKeyboardMarkup(
        [
            ["Изменить время утреннего напоминания",
             "Изменить время вечернего напоминания"],
            ["Изменить день начала недели",
             "Уведомления о пропусках"],
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

# def get_morning_completed_keyboard():
#     return ReplyKeyboardMarkup(
#         [
#             ["Посмотреть сегодняшние ответы"],
#             ["Заполнить утро заново"],
#             [BACK_BUTTON],
#         ],
#         resize_keyboard=True,
#         one_time_keyboard=True,
#     )
