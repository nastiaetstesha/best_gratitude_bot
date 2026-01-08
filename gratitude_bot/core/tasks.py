from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import logging
from celery import shared_task
from django.conf import settings as dj_settings

from telegram import Bot
from core.models import UserSettings, DailyEntry

logger = logging.getLogger(__name__)


def _send_tg(chat_id: int, text: str) -> None:
    token = getattr(dj_settings, "TELEGRAM_BOT_TOKEN", None)
    if not token:
        logger.warning("NO TELEGRAM_BOT_TOKEN in settings. Can't send to %s", chat_id)
        return
    try:
        Bot(token=token).send_message(chat_id=chat_id, text=text)
        logger.info("SENT to chat_id=%s: %s", chat_id, text[:80])
    except Exception:
        logger.exception("FAILED sending to chat_id=%s", chat_id)


def _local_now(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


@shared_task
def tick_reminders():
    qs = UserSettings.objects.select_related("user").all()

    for s in qs:
        user = s.user
        tz = ZoneInfo(s.timezone)
        now = _local_now(s.timezone)
        today = now.date()
        hhmm = now.strftime("%H:%M")

        # ВАЖНО: entry создаём один раз и используем дальше
        entry, _ = DailyEntry.objects.get_or_create(user=user, date=today)

        logger.info(
            "tick user=%s tz=%s local=%s morning=%s(%s) evening=%s(%s) entry(m=%s e=%s)",
            user.telegram_id,
            s.timezone,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            s.morning_time.strftime("%H:%M"),
            s.morning_enabled,
            s.evening_time.strftime("%H:%M"),
            s.evening_enabled,
            entry.completed_morning,
            entry.completed_evening,
        )

        # --- утро ---
        morning_target = datetime.combine(today, s.morning_time, tzinfo=tz)
        morning_delta = (now - morning_target).total_seconds()
        logger.info(
            "morning check user=%s now=%s target=%s delta=%.3f completed=%s",
            user.telegram_id,
            now.strftime("%H:%M:%S"),
            morning_target.strftime("%H:%M:%S"),
            morning_delta,
            entry.completed_morning,
        )
        if s.morning_enabled and 0 <= morning_delta < 120:
            if not entry.completed_morning:
                _send_tg(user.telegram_id, "☀️ Доброе утро! Пора заполнить утренний блок 🌿")

        # --- вечер ---
        evening_target = datetime.combine(today, s.evening_time, tzinfo=tz)
        evening_delta = (now - evening_target).total_seconds()
        logger.info(
            "evening check user=%s now=%s target=%s delta=%.3f completed=%s",
            user.telegram_id,
            now.strftime("%H:%M:%S"),
            evening_target.strftime("%H:%M:%S"),
            evening_delta,
            entry.completed_evening,
        )
        if s.evening_enabled and 0 <= evening_delta < 120:
            if not entry.completed_evening:
                _send_tg(user.telegram_id, "🌙 Добрый вечер! Пора заполнить вечерний блок ✨")

        # --- пропуски (мягко) ---
        if s.notify_missed_days and hhmm == "12:00":
            yesterday = today - timedelta(days=1)
            e = DailyEntry.objects.filter(user=user, date=yesterday).first()
            missed = (not e) or (not e.completed_morning and not e.completed_evening)
            logger.info("missed-check user=%s missed=%s", user.telegram_id, missed)
            if missed:
                _send_tg(user.telegram_id, "🫶 Вчера был пропуск. Хочешь вернуться сегодня? Я рядом.")
