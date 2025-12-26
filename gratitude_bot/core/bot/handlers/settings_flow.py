# gratitude_bot/core/bot/handlers/settings_flow.py

from __future__ import annotations

import re
from datetime import time

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from core.bot.handlers.utils import get_or_create_tg_user, get_user_settings
from core.bot.keyboards.main_menu import (
    BACK_BUTTON,
    get_main_menu_keyboard,
    get_settings_menu_keyboard,
)

# ---------- buttons text (должны совпадать с main_menu.py) ----------
SET_TZ_BUTTON = "Часовой пояс"
SET_TZ_OTHER = "Другое (ввести вручную)"

SET_MORNING_TIME_BUTTON = "Время утреннего напоминания"
SET_EVENING_TIME_BUTTON = "Время вечернего напоминания"
SET_WEEK_START_BUTTON = "День начала недели"

TOGGLE_MORNING_BUTTON = "Утренние напоминания: вкл/выкл"
TOGGLE_EVENING_BUTTON = "Вечерние напоминания: вкл/выкл"
TOGGLE_MISSED_BUTTON = "Уведомления о пропусках: вкл/выкл"


# ---------- timezone constants (храним IANA-строки!) ----------
TZ_MOSCOW = "Europe/Moscow"
TZ_UTC = "UTC"

TZ_CHOOSE_MOSCOW = "Москва (Europe/Moscow)"
TZ_CHOOSE_UTC = "UTC"

# Кнопки пользователю показываем "UTC+3", а сохраняем IANA "Etc/GMT-3" (знак инвертирован!)
def _utc_offset_to_iana(offset: int) -> str:
    """
    offset: +3 означает UTC+3
    return: IANA string "Etc/GMT-3"
    """
    if offset == 0:
        return TZ_UTC
    if offset > 0:
        return f"Etc/GMT-{offset}"
    return f"Etc/GMT+{abs(offset)}"


def _format_utc_button(offset: int) -> str:
    if offset == 0:
        return "UTC"
    sign = "+" if offset > 0 else "-"
    return f"UTC{sign}{abs(offset)}"


# ---------- states ----------
SETTINGS_MENU = 501
SETTINGS_TZ_CHOOSE = 502
SETTINGS_TZ_INPUT = 503
SETTINGS_MORNING_TIME_INPUT = 504
SETTINGS_EVENING_TIME_INPUT = 505
SETTINGS_WEEK_START_CHOOSE = 506

_TIME_RE = re.compile(r"^\s*(\d{1,2})\s*:\s*(\d{2})\s*$")


# ---------- keyboards ----------
def get_timezone_keyboard() -> ReplyKeyboardMarkup:
    """
    Кнопки:
    - Москва
    - UTC
    - популярные UTC-офсеты
    - Другое (ручной ввод IANA)
    """
    rows = [
        [TZ_CHOOSE_MOSCOW],
        [TZ_CHOOSE_UTC],
    ]

    # Сделаем сетку офсетов -12..-1 и +1..+14 (без половинок — их вводят вручную)
    neg = list(range(-12, 0))   # -12..-1
    pos = list(range(1, 15))    # +1..+14

    def chunk(items, n=4):
        for i in range(0, len(items), n):
            yield items[i:i+n]

    for part in chunk(neg, 4):
        rows.append([_format_utc_button(x) for x in part])

    for part in chunk(pos, 4):
        rows.append([_format_utc_button(x) for x in part])

    rows.append([SET_TZ_OTHER])
    rows.append([BACK_BUTTON])

    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


def get_week_start_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        ["Понедельник", "Вторник"],
        ["Среда", "Четверг"],
        ["Пятница", "Суббота"],
        ["Воскресенье"],
        [BACK_BUTTON],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


# ---------- menu entry / cancel ----------
def settings_menu(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Настройки ⚙️\nЧто меняем?",
        reply_markup=get_settings_menu_keyboard(),
    )
    return SETTINGS_MENU


def settings_cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Ок, верну в меню 👇", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


# ---------- time helpers ----------
def _parse_hhmm(text: str) -> time | None:
    m = _TIME_RE.match(text or "")
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None
    return time(hh, mm)


def _format_time(t: time) -> str:
    return f"{t.hour:02}:{t.minute:02}"


# ---------- toggles ----------
def toggle_morning(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    s.morning_enabled = not s.morning_enabled
    s.save(update_fields=["morning_enabled"])
    status = "включены ✅" if s.morning_enabled else "выключены ❌"
    update.message.reply_text(
        f"☀️ Утренние напоминания {status}",
        reply_markup=get_settings_menu_keyboard(),
    )
    return SETTINGS_MENU


def toggle_evening(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    s.evening_enabled = not s.evening_enabled
    s.save(update_fields=["evening_enabled"])
    status = "включены ✅" if s.evening_enabled else "выключены ❌"
    update.message.reply_text(
        f"🌙 Вечерние напоминания {status}",
        reply_markup=get_settings_menu_keyboard(),
    )
    return SETTINGS_MENU


def toggle_missed(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    s.notify_missed_days = not s.notify_missed_days
    s.save(update_fields=["notify_missed_days"])
    status = "включены ✅" if s.notify_missed_days else "выключены ❌"
    update.message.reply_text(
        f"🔔 Уведомления о пропусках {status}",
        reply_markup=get_settings_menu_keyboard(),
    )
    return SETTINGS_MENU


# ---------- morning time ----------
def set_morning_time_start(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    update.message.reply_text(
        "☀️ Введи время утреннего напоминания в формате HH:MM\n"
        f"Сейчас: {_format_time(s.morning_time)}\n"
        "Например: 08:30",
        reply_markup=ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True, one_time_keyboard=False),
    )
    return SETTINGS_MORNING_TIME_INPUT


def set_morning_time_input(update: Update, context: CallbackContext):
    if (update.message.text or "").strip() == BACK_BUTTON:
        return settings_menu(update, context)

    t = _parse_hhmm(update.message.text)
    if not t:
        update.message.reply_text("❌ Не поняла. Введи время как HH:MM (например 08:30) или нажми «Назад».")
        return SETTINGS_MORNING_TIME_INPUT

    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    s.morning_time = t
    s.save(update_fields=["morning_time"])

    update.message.reply_text(
        f"✅ Утреннее напоминание установлено на {_format_time(t)}",
        reply_markup=get_settings_menu_keyboard(),
    )
    return SETTINGS_MENU


# ---------- evening time ----------
def set_evening_time_start(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    update.message.reply_text(
        "🌙 Введи время вечернего напоминания в формате HH:MM\n"
        f"Сейчас: {_format_time(s.evening_time)}\n"
        "Например: 21:00",
        reply_markup=ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True, one_time_keyboard=False),
    )
    return SETTINGS_EVENING_TIME_INPUT


def set_evening_time_input(update: Update, context: CallbackContext):
    if (update.message.text or "").strip() == BACK_BUTTON:
        return settings_menu(update, context)

    t = _parse_hhmm(update.message.text)
    if not t:
        update.message.reply_text("❌ Не поняла. Введи время как HH:MM (например 21:00) или нажми «Назад».")
        return SETTINGS_EVENING_TIME_INPUT

    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    s.evening_time = t
    s.save(update_fields=["evening_time"])

    update.message.reply_text(
        f"✅ Вечернее напоминание установлено на {_format_time(t)}",
        reply_markup=get_settings_menu_keyboard(),
    )
    return SETTINGS_MENU


# ---------- week start ----------
_WEEK_START_MAP = {
    "Понедельник": 1,
    "Вторник": 2,
    "Среда": 3,
    "Четверг": 4,
    "Пятница": 5,
    "Суббота": 6,
    "Воскресенье": 7,
}


def set_week_start_start(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    current = {v: k for k, v in _WEEK_START_MAP.items()}.get(s.week_start, "Понедельник")

    update.message.reply_text(
        f"📅 Выбери день начала недели.\nСейчас: {current}",
        reply_markup=get_week_start_keyboard(),
    )
    return SETTINGS_WEEK_START_CHOOSE


def set_week_start_choose(update: Update, context: CallbackContext):
    text = (update.message.text or "").strip()
    if text == BACK_BUTTON:
        return settings_menu(update, context)

    if text not in _WEEK_START_MAP:
        update.message.reply_text("Не понял выбор. Нажми кнопку 👇", reply_markup=get_week_start_keyboard())
        return SETTINGS_WEEK_START_CHOOSE

    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    s.week_start = _WEEK_START_MAP[text]
    s.save(update_fields=["week_start"])

    update.message.reply_text(
        f"✅ Неделя теперь начинается с: {text}",
        reply_markup=get_settings_menu_keyboard(),
    )
    return SETTINGS_MENU


# ---------- timezone ----------
def timezone_start(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    update.message.reply_text(
        "🕒 Выбери часовой пояс.\n"
        f"Сейчас: {s.timezone}\n\n"
        "Если нужен нестандартный (например UTC+9:30) — нажми «Другое» и введи IANA-строку.",
        reply_markup=get_timezone_keyboard(),
    )
    return SETTINGS_TZ_CHOOSE


def timezone_choose(update: Update, context: CallbackContext):
    text = (update.message.text or "").strip()

    if text == BACK_BUTTON:
        return settings_menu(update, context)

    user = get_or_create_tg_user(update)
    s = get_user_settings(user)

    if text == TZ_CHOOSE_MOSCOW:
        s.timezone = TZ_MOSCOW
        s.save(update_fields=["timezone"])
        update.message.reply_text(
            f"✅ Часовой пояс установлен: {s.timezone}",
            reply_markup=get_settings_menu_keyboard(),
        )
        return SETTINGS_MENU

    if text == TZ_CHOOSE_UTC:
        s.timezone = TZ_UTC
        s.save(update_fields=["timezone"])
        update.message.reply_text(
            f"✅ Часовой пояс установлен: {s.timezone}",
            reply_markup=get_settings_menu_keyboard(),
        )
        return SETTINGS_MENU

    if text == SET_TZ_OTHER:
        update.message.reply_text(
            "✍️ Введи часовой пояс в формате IANA.\n"
            "Примеры:\n"
            "• Europe/Nicosia\n"
            "• Europe/Athens\n"
            "• America/New_York\n"
            "• Asia/Tokyo\n\n"
            "Важно: формат вида UTC+3 не поддерживается как IANA.\n"
            "Для UTC+3 выбери кнопку «UTC+3».",
            reply_markup=ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True, one_time_keyboard=False),
        )
        return SETTINGS_TZ_INPUT

    # кнопки вида UTC+3 / UTC-2
    if text.startswith("UTC"):
        # UTC+N / UTC-N
        m = re.match(r"^UTC([+-])(\d{1,2})$", text)
        if not m:
            update.message.reply_text("Не понял выбор. Нажми кнопку 👇", reply_markup=get_timezone_keyboard())
            return SETTINGS_TZ_CHOOSE

        sign = m.group(1)
        val = int(m.group(2))
        offset = val if sign == "+" else -val
        tz_name = _utc_offset_to_iana(offset)

        s.timezone = tz_name
        s.save(update_fields=["timezone"])

        update.message.reply_text(
            f"✅ Часовой пояс установлен: {text} ({s.timezone})",
            reply_markup=get_settings_menu_keyboard(),
        )
        return SETTINGS_MENU

    update.message.reply_text("Не понял выбор. Нажми кнопку 👇", reply_markup=get_timezone_keyboard())
    return SETTINGS_TZ_CHOOSE


def timezone_input(update: Update, context: CallbackContext):
    text = (update.message.text or "").strip()
    if text == BACK_BUTTON:
        return timezone_start(update, context)

    # Простейшая валидация на "похоже на IANA"
    # (полную валидацию через ZoneInfo можно делать в твоём get_user_tz — ты уже так делаешь)
    if "/" not in text and text != "UTC":
        update.message.reply_text(
            "❌ Похоже, это не IANA-строка.\n"
            "Пример: Europe/Nicosia или America/New_York.\n"
            "Попробуй ещё раз или нажми «Назад»."
        )
        return SETTINGS_TZ_INPUT

    user = get_or_create_tg_user(update)
    s = get_user_settings(user)
    s.timezone = text
    s.save(update_fields=["timezone"])

    update.message.reply_text(
        f"✅ Часовой пояс установлен: {s.timezone}",
        reply_markup=get_settings_menu_keyboard(),
    )
    return SETTINGS_MENU
