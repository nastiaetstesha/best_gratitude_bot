from telegram import Update
from telegram.ext import CallbackContext

from core.bot.keyboards.main_menu import get_week_menu_keyboard


def week_menu(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Неделя 📆",
        reply_markup=get_week_menu_keyboard(),
    )
