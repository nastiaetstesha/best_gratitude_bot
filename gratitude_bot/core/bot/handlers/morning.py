from telegram import Update
from telegram.ext import CallbackContext

from core.bot.keyboards.main_menu import get_cancel_keyboard


def morning_start(update: Update, context: CallbackContext):
    """
    Точка входа в утренний блок
    """
    update.message.reply_text(
        "☀️ Утренний фокус\n\n"
        "Сейчас будет несколько коротких вопросов.",
        reply_markup=get_cancel_keyboard(),
    )

    # TODO: перейти к первому вопросу
    # update.message.reply_text(
    #     "Вопрос 1: За что вы сегодня благодарны?",
    # )