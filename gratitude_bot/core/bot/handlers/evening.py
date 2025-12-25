from telegram import Update
from telegram.ext import CallbackContext

from core.bot.keyboards.main_menu import get_cancel_keyboard


def evening_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🌙 Вечерняя рефлексия\n\n"
        "Подведём итоги дня.",
        reply_markup=get_cancel_keyboard(),
    )

    # TODO: вопросы благодарности
