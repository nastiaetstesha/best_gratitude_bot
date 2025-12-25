from telegram import Update
from telegram.ext import CallbackContext

from core.bot.keyboards.main_menu import (
    get_main_menu_keyboard,
    get_today_menu_keyboard,
)


def start(update: Update, context: CallbackContext):
    user = update.effective_user

    update.message.reply_text(
        (
            f"Привет, {user.first_name or 'друг'} 👋\n\n"
            "Это дневник благодарности и фокуса.\n"
            "2–5 минут в день — чтобы лучше чувствовать себя и свою жизнь.\n\n"
            "Начнём?"
        ),
        reply_markup=get_main_menu_keyboard(),
    )


def back_to_main_menu(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Главное меню 👇",
        reply_markup=get_main_menu_keyboard(),
    )


def today_menu(update: Update, context: CallbackContext):
    """
    Экран «Сегодня» — сюда позже добавим стрик и статус дня
    """
    # позже сюда добавим расчёт стрика и статуса
    update.message.reply_text(
        "Сегодняшний день 🌱\n\n"
        "Что сделаем?",
        reply_markup=get_today_menu_keyboard(),
    )
