from datetime import datetime
from zoneinfo import ZoneInfo
from django.utils import timezone

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from core.models import TelegramUser, UserSettings, DailyEntry
from core.bot.keyboards.main_menu import (
    SKIP_TODAY_BUTTON,
    get_today_menu_keyboard,
)

def _get_user(update: Update) -> TelegramUser:
    tg_id = update.effective_user.id
    return TelegramUser.objects.get(telegram_id=tg_id)

def _local_today(tz_name: str):
    return datetime.now(ZoneInfo(tz_name)).date()

def skip_today(update: Update, context: CallbackContext):
    user = _get_user(update)
    settings = UserSettings.objects.get(user=user)

    today = _local_today(settings.timezone)

    entry, _ = DailyEntry.objects.get_or_create(user=user, date=today)
    entry.skipped = True
    entry.skipped_at = timezone.now()
    entry.save(update_fields=["skipped", "skipped_at"])

    update.message.reply_text(
        "Ок, сегодня пропускаем ✅\n\n"
        "Если позже появятся силы — можешь вернуться и заполнить утро/вечер даже одним предложением. "
        "Я рядом 🤍",
        reply_markup=get_today_menu_keyboard(),
    )
    return ConversationHandler.END