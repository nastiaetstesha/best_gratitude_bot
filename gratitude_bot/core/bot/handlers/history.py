from telegram import Update
from telegram.ext import CallbackContext

from core.bot.keyboards.main_menu import get_history_menu_keyboard


def history_menu(update: Update, context: CallbackContext):
    update.message.reply_text(
        "История записей 📖",
        reply_markup=get_history_menu_keyboard(),
    )
