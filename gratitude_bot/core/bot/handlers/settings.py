from telegram import Update
from telegram.ext import CallbackContext

from core.bot.keyboards.main_menu import get_settings_menu_keyboard


def settings_menu(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Настройки ⚙️",
        reply_markup=get_settings_menu_keyboard(),
    )

