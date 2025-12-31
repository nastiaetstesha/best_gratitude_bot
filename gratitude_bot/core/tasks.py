# gratitude_bot/core/tasks.py
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from celery import shared_task
from django.conf import settings as dj_settings

from telegram import Bot

from core.models import UserSettings, DailyEntry


def _send_tg(chat_id: int, text: str) -> None:
    token = getattr(dj_settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        return
    Bot(token=token).send_message(chat_id=chat_id, text=text)


def _local_now(tz_name: str) -> datetime:
    # tz_name должен быть валидным IANA (Europe/Moscow) или UTC+X (если ты так разрешишь)
    return datetime.now(ZoneInfo(tz_name))


@shared_task
def tick_reminders():
    """
    Запускается по расписанию (например раз в минуту) и решает,
    кому надо отправить напоминание прямо сейчас.
    """
    qs = UserSettings.objects.select_related("user").all()

    for s in qs:
        user = s.user
        now = _local_now(s.timezone)
        hhmm = now.strftime("%H:%M")
        today = now.date()

        # --- утро ---
        if s.morning_enabled and hhmm == s.morning_time.strftime("%H:%M"):
            entry, _ = DailyEntry.objects.get_or_create(user=user, date=today)
            if not entry.completed_morning:
                _send_tg(user.telegram_id, "☀️ Доброе утро! Пора заполнить утренний блок 🌿")

        # --- вечер ---
        if s.evening_enabled and hhmm == s.evening_time.strftime("%H:%M"):
            entry, _ = DailyEntry.objects.get_or_create(user=user, date=today)
            if not entry.completed_evening:
                _send_tg(user.telegram_id, "🌙 Добрый вечер! Пора заполнить вечерний блок ✨")

        # --- пропуски (мягко) ---
        # пример: в 12:00 локального времени напоминаем, если вчера не заполнено ничего
        if s.notify_missed_days and hhmm == "12:00":
            yesterday = today - timedelta(days=1)
            e = DailyEntry.objects.filter(user=user, date=yesterday).first()
            if not e or (not e.completed_morning and not e.completed_evening):
                _send_tg(user.telegram_id, "🫶 Вчера был пропуск. Хочешь вернуться сегодня? Я рядом.")
