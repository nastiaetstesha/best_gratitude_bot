# gratitude_bot/core/bot/bot.py
import os
import logging

from django.conf import settings

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    Filters,
)
from core.bot.handlers.today import skip_today
from core.bot.keyboards.main_menu import SKIP_TODAY_BUTTON

from telegram.ext import MessageHandler, Filters, CommandHandler

from core.bot.handlers.common import start, back_to_main_menu, today_menu, help
from telegram.ext import ConversationHandler

from telegram.ext import ConversationHandler

from core.bot.handlers.morning_flow import (
    morning_start,
    morning_handle_answer,
    morning_cancel,
    morning_redo,
    view_today_answers,
    MORNING_ANSWER,
    MORNING_REDO_BUTTON,
    VIEW_TODAY_ANSWERS,
)

from core.bot.handlers.evening_flow import (
    evening_start,
    evening_handle_answer,
    evening_cancel,
    EV_GRAT_1,
    EV_GRAT_2,
    EV_GRAT_3,
    EV_BEST,
)
from core.bot.handlers.week_flow import (
    week_menu,
    week_fill_start,
    week_handle_mid,
    week_handle_final,
    week_cancel,
    week_task_show,
    week_view,
    week_redo,
    WEEK_FILL_BUTTON,
    WEEK_VIEW_BUTTON,
    WEEK_TASK_BUTTON,
    WEEK_REDO_BUTTON,
    WEEK_MID,
    WEEK_FINAL,
)

from core.bot.handlers.history_flow import (
    history_menu,
    history_by_date_start,
    history_date_choose,
    history_date_input,
    history_progress,
    history_search_start,
    history_search_input,
    history_cancel,
    HISTORY_MENU,
    HISTORY_DATE_CHOOSE,
    HISTORY_DATE_INPUT,
    HISTORY_SEARCH_INPUT,
)
from core.bot.keyboards.main_menu import (
    HISTORY_BY_DATE_BUTTON,
    HISTORY_PROGRESS_BUTTON,
    HISTORY_SEARCH_BUTTON,
)
from core.bot.handlers.statistics_flow import (
    statistics_menu,
    statistics_cancel,
    statistics_general,
    statistics_fill_chart,
    statistics_topics,
    statistics_weekdays,
    STATS_MENU,
    STATS_GENERAL_BUTTON,
    STATS_CHART_BUTTON,
    STATS_TOPICS_BUTTON,
    STATS_WEEKDAYS_BUTTON,
)
from core.bot.handlers.settings_flow import (
    settings_menu,
    settings_cancel,
    # settings_morning_time_save,
    # settings_evening_time_start,
    # settings_evening_time_save,
    # settings_week_start,
    # settings_week_start_save,
    # settings_notify_toggle,
    SETTINGS_MENU,
    # SETTINGS_MORNING_TIME,
    # SETTINGS_EVENING_TIME,
    # SETTINGS_WEEK_START,
)
from core.bot.handlers.settings_flow import (
    settings_menu,
    settings_cancel,
    timezone_start,
    timezone_choose,
    timezone_input,
    set_morning_time_start,
    set_morning_time_input,
    set_evening_time_start,
    set_evening_time_input,
    set_week_start_start,
    set_week_start_choose,
    toggle_morning,
    toggle_evening,
    toggle_missed,
    SETTINGS_MENU,
    SETTINGS_TZ_CHOOSE,
    SETTINGS_TZ_INPUT,
    SETTINGS_MORNING_TIME_INPUT,
    SETTINGS_EVENING_TIME_INPUT,
    SETTINGS_WEEK_START_CHOOSE,
)

from core.bot.handlers.settings_flow import (
    SET_TZ_BUTTON,
    SET_MORNING_TIME_BUTTON,
    SET_EVENING_TIME_BUTTON,
    SET_WEEK_START_BUTTON,
    TOGGLE_MORNING_BUTTON,
    TOGGLE_EVENING_BUTTON,
    TOGGLE_MISSED_BUTTON,
)

from core.bot.keyboards.main_menu import (
    BACK_BUTTON,
)
logger = logging.getLogger(__name__)


# def start(update, context):
#     """Простой /start и показ главного меню."""
#     user = update.effective_user
#     update.message.reply_text(
#         f"Привет, {user.first_name or 'друг'}! Это бот c ??? 🤖",
#         reply_markup=get_main_menu_keyboard(),
# )

# def back_to_main_menu(update, context):
#     """Общий обработчик кнопки 'Назад' – возвращает в главное меню."""
#     update.message.reply_text(
#         "Окей, вернёмся в меню",
#         reply_markup=get_main_menu_keyboard(),
#     )


def build_updater() -> Updater:
    # токен берём из настроек Django
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None) or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан ни в settings, ни в переменных окружения")

    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    # /start
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    history_conv = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(r"^История$"), history_menu),
    ],
    states={
        HISTORY_MENU: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), history_cancel),

            MessageHandler(Filters.regex(rf"^{HISTORY_BY_DATE_BUTTON}$"), history_by_date_start),
            MessageHandler(Filters.regex(rf"^{HISTORY_PROGRESS_BUTTON}$"), history_progress),
            MessageHandler(Filters.regex(rf"^{HISTORY_SEARCH_BUTTON}$"), history_search_start),
        ],
        HISTORY_DATE_CHOOSE: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), history_menu),  # назад в историю
            MessageHandler(Filters.text & ~Filters.command, history_date_choose),
        ],
        HISTORY_DATE_INPUT: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), history_menu),
            MessageHandler(Filters.text & ~Filters.command, history_date_input),
        ],
        HISTORY_SEARCH_INPUT: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), history_menu),
            MessageHandler(Filters.text & ~Filters.command, history_search_input),
        ],
    },
    fallbacks=[],
    allow_reentry=True,
    )
    dp.add_handler(history_conv)

    dp.add_handler(MessageHandler(Filters.regex(r"^Сегодня$"), today_menu))
    # dp.add_handler(MessageHandler(Filters.regex(r"^Утро$"), morning_start))
    # dp.add_handler(MessageHandler(Filters.regex(r"^Вечер$"), evening_start))
    dp.add_handler(MessageHandler(Filters.regex(rf"^{SKIP_TODAY_BUTTON}$"), skip_today))
    dp.add_handler(MessageHandler(Filters.regex(r"^Неделя$"), week_menu))
    # dp.add_handler(MessageHandler(Filters.regex(r"^История$"), history_menu))
    stats_conv = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex(r"^Статистика$"), statistics_menu)],
    states={
        STATS_MENU: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), statistics_cancel),

            MessageHandler(Filters.regex(rf"^{STATS_GENERAL_BUTTON}$"), statistics_general),
            MessageHandler(Filters.regex(rf"^{STATS_CHART_BUTTON}$"), statistics_fill_chart),
            MessageHandler(Filters.regex(rf"^{STATS_TOPICS_BUTTON}$"), statistics_topics),
            MessageHandler(Filters.regex(rf"^{STATS_WEEKDAYS_BUTTON}$"), statistics_weekdays),
        ],
    },
    fallbacks=[],
    allow_reentry=True,
    )
    dp.add_handler(stats_conv)

    settings_conv = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(r"^Настройки$"), settings_menu),
    ],
    states={
        SETTINGS_MENU: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), settings_cancel),

            MessageHandler(Filters.regex(rf"^{SET_TZ_BUTTON}$"), timezone_start),

            MessageHandler(Filters.regex(rf"^{SET_MORNING_TIME_BUTTON}$"), set_morning_time_start),
            MessageHandler(Filters.regex(rf"^{SET_EVENING_TIME_BUTTON}$"), set_evening_time_start),

            MessageHandler(Filters.regex(rf"^{SET_WEEK_START_BUTTON}$"), set_week_start_start),

            MessageHandler(Filters.regex(rf"^{TOGGLE_MORNING_BUTTON}$"), toggle_morning),
            MessageHandler(Filters.regex(rf"^{TOGGLE_EVENING_BUTTON}$"), toggle_evening),
            MessageHandler(Filters.regex(rf"^{TOGGLE_MISSED_BUTTON}$"), toggle_missed),
        ],
        SETTINGS_TZ_CHOOSE: [
            MessageHandler(Filters.text & ~Filters.command, timezone_choose),
        ],
        SETTINGS_TZ_INPUT: [
            MessageHandler(Filters.text & ~Filters.command, timezone_input),
        ],
        SETTINGS_MORNING_TIME_INPUT: [
            MessageHandler(Filters.text & ~Filters.command, set_morning_time_input),
        ],
        SETTINGS_EVENING_TIME_INPUT: [
            MessageHandler(Filters.text & ~Filters.command, set_evening_time_input),
        ],
        SETTINGS_WEEK_START_CHOOSE: [
            MessageHandler(Filters.text & ~Filters.command, set_week_start_choose),
        ],
    },
    fallbacks=[],
    allow_reentry=True,
    )

    dp.add_handler(settings_conv)

    morning_conv = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(r"^Утро$"), morning_start),
        MessageHandler(Filters.regex(r"^Заполнить утро$"), morning_start),
    ],
    states={
        MORNING_ANSWER: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), morning_cancel),  # <-- ВАЖНО: первым
            MessageHandler(Filters.text & ~Filters.command, morning_handle_answer),
        ],
    },
    fallbacks=[],
    allow_reentry=True,
)
    dp.add_handler(morning_conv)


    # Кнопки вне активного диалога (когда утро уже заполнено)
    dp.add_handler(MessageHandler(Filters.regex(rf"^{MORNING_REDO_BUTTON}$"), morning_redo))
    dp.add_handler(MessageHandler(Filters.regex(rf"^{VIEW_TODAY_ANSWERS}$"), view_today_answers))

    evening_conv = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(r"^Вечер$"), evening_start),
        MessageHandler(Filters.regex(r"^Заполнить вечер$"), evening_start),
    ],
    states={
    EV_GRAT_1: [
        MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), evening_cancel),
        MessageHandler(Filters.text & ~Filters.command, evening_handle_answer),
    ],
    EV_GRAT_2: [
        MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), evening_cancel),
        MessageHandler(Filters.text & ~Filters.command, evening_handle_answer),
    ],
    EV_GRAT_3: [
        MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), evening_cancel),
        MessageHandler(Filters.text & ~Filters.command, evening_handle_answer),
    ],
    EV_BEST: [
        MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), evening_cancel),
        MessageHandler(Filters.text & ~Filters.command, evening_handle_answer),
    ],
    },
    fallbacks=[],
    allow_reentry=True,
    )
    dp.add_handler(evening_conv)

    # history_conv = ConversationHandler(
    # entry_points=[
    #     MessageHandler(Filters.regex(r"^История$"), history_menu),
    # ],
    # states={
    #     HISTORY_MENU: [
    #         MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), history_cancel),

    #         MessageHandler(Filters.regex(rf"^{HISTORY_BY_DATE_BUTTON}$"), history_by_date_start),
    #         MessageHandler(Filters.regex(rf"^{HISTORY_PROGRESS_BUTTON}$"), history_progress),
    #         MessageHandler(Filters.regex(rf"^{HISTORY_SEARCH_BUTTON}$"), history_search_start),
    #     ],
    #     HISTORY_DATE_CHOOSE: [
    #         MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), history_menu),  # назад в историю
    #         MessageHandler(Filters.text & ~Filters.command, history_date_choose),
    #     ],
    #     HISTORY_DATE_INPUT: [
    #         MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), history_menu),
    #         MessageHandler(Filters.text & ~Filters.command, history_date_input),
    #     ],
    #     HISTORY_SEARCH_INPUT: [
    #         MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), history_menu),
    #         MessageHandler(Filters.text & ~Filters.command, history_search_input),
    #     ],
    # },
    # fallbacks=[],
    # allow_reentry=True,
    # )
    # dp.add_handler(history_conv)

    # dp.add_handler(
    #     MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), back_to_main_menu)
    # )
    week_conv = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(rf"^{WEEK_FILL_BUTTON}$"), week_fill_start),
        MessageHandler(Filters.regex(r"^Заполнить неделю$"), week_fill_start),  # если у тебя так в клавиатуре
    ],
    states={
        WEEK_MID: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), week_cancel),
            MessageHandler(Filters.text & ~Filters.command, week_handle_mid),
        ],
        WEEK_FINAL: [
            MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), week_cancel),
            MessageHandler(Filters.text & ~Filters.command, week_handle_final),
        ],
    },
    fallbacks=[],
    allow_reentry=True,
    )
    dp.add_handler(week_conv)

    dp.add_handler(MessageHandler(Filters.regex(rf"^{WEEK_VIEW_BUTTON}$"), week_view))
    dp.add_handler(MessageHandler(Filters.regex(rf"^{WEEK_TASK_BUTTON}$"), week_task_show))
    dp.add_handler(MessageHandler(Filters.regex(rf"^{WEEK_REDO_BUTTON}$"), week_redo))
    dp.add_handler(
        MessageHandler(Filters.regex(rf"^{BACK_BUTTON}$"), back_to_main_menu)
    )
        
    logger.info("Handlers registered")
    return updater