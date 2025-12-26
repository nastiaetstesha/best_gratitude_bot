# gratitude_bot/core/bot/handlers/history_flow.py
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from django.db.models import Q

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from core.models import DailyEntry, Answer, WeeklyCycle, QuestionTemplate
from core.bot.handlers.utils import get_or_create_tg_user, user_local_date
from core.bot.keyboards.main_menu import (
    get_main_menu_keyboard,
    BACK_BUTTON,
    HISTORY_BY_DATE_BUTTON,
    HISTORY_PROGRESS_BUTTON,
    HISTORY_SEARCH_BUTTON,
)

# ---------- states ----------
HISTORY_MENU = 301
HISTORY_DATE_CHOOSE = 302
HISTORY_DATE_INPUT = 303
HISTORY_SEARCH_INPUT = 304

_NUM_PREFIX_RE = re.compile(r"^\s*\d+\)\s*")
_DATE_RE = re.compile(r"^\s*(\d{2})\.(\d{2})\.(\d{4})\s*$")


def _parse_date_ddmmyyyy(text: str) -> date | None:
    m = _DATE_RE.match(text or "")
    if not m:
        return None
    try:
        return datetime.strptime(m.group(0).strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


# ---------- text helpers ----------
def _clean_question_text(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "—"

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "—"

    if len(lines) >= 2 and lines[0] in ("☀️ Утро", "🌙 Вечер", "🗓️ Неделя", "Неделя"):
        candidate = lines[1]
    else:
        candidate = lines[0]

    candidate = _NUM_PREFIX_RE.sub("", candidate).strip()
    return candidate or "—"


def _infer_period(answer: Answer) -> str:
    period = getattr(answer.question, "period", None)
    if period in (
        QuestionTemplate.PERIOD_MORNING,
        QuestionTemplate.PERIOD_EVENING,
        QuestionTemplate.PERIOD_WEEKLY,
    ):
        return period

    qt = (answer.question_text or "").lower()
    if "утро" in qt or "☀️" in qt:
        return QuestionTemplate.PERIOD_MORNING
    if "вечер" in qt or "🌙" in qt:
        return QuestionTemplate.PERIOD_EVENING

    return "other"


def _format_answers_block(title: str, answers: list[Answer]) -> str:
    if not answers:
        return ""
    parts = [title]
    for a in answers:
        q = _clean_question_text(a.question_text)
        parts.append(f"❓ {q}\n→ {a.answer_text}")
    return "\n".join(parts)


# ---------- keyboards ----------
def get_history_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [HISTORY_BY_DATE_BUTTON],
            [HISTORY_PROGRESS_BUTTON, HISTORY_SEARCH_BUTTON],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_date_choose_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Сегодня", "Вчера"],
            ["Позавчера"],
            ["Ввести дату (ДД.ММ.ГГГГ)"],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_date_input_keyboard():
    # в режиме ввода даты оставим минимум, чтобы не “ломать” state случайными кнопками
    return ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True, one_time_keyboard=False)


# ---------- entry ----------
def history_menu(update: Update, context: CallbackContext):
    update.message.reply_text(
        "История записей 📖\nЧто делаем?",
        reply_markup=get_history_menu_keyboard(),
    )
    return HISTORY_MENU


def history_cancel(update: Update, context: CallbackContext):
    context.user_data.pop("history_date", None)
    update.message.reply_text("Ок, верну в меню 👇", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


# ---------- by date flow ----------
def history_by_date_start(update: Update, context: CallbackContext):
    context.user_data.pop("history_date", None)
    update.message.reply_text("Выбери дату 👇", reply_markup=get_date_choose_keyboard())
    return HISTORY_DATE_CHOOSE


def history_show_by_date(update: Update, context: CallbackContext, picked_date: date):
    """
    ЕДИНАЯ функция показа ответов за дату.
    Важно: после показа ВСЕГДА возвращаем HISTORY_DATE_CHOOSE и снова показываем клавиатуру.
    """
    user = get_or_create_tg_user(update)

    parts: list[str] = [f"📅 {picked_date:%d.%m.%Y}\n"]

    entry = DailyEntry.objects.filter(user=user, date=picked_date).first()
    if entry:
        parts.append(_format_daily_entry(entry))
    else:
        parts.append(f"За {picked_date:%d.%m.%Y} записей нет.")

    cycle = (
        WeeklyCycle.objects.filter(user=user, week_start__lte=picked_date, week_end__gte=picked_date)
        .select_related("task")
        .first()
    )
    if cycle:
        parts.append("")
        parts.append(_format_weekly_cycle(cycle))

    update.message.reply_text("\n".join(parts))

    # ✅ всегда возвращаем в CHOOSE
    update.message.reply_text("Выбери дату 👇", reply_markup=get_date_choose_keyboard())
    return HISTORY_DATE_CHOOSE


def history_date_choose(update: Update, context: CallbackContext):
    text = (update.message.text or "").strip()

    if text == BACK_BUTTON:
        return history_menu(update, context)

    # если человек случайно нажал “Посмотреть ответы за дату” уже находясь в выборе — просто остаёмся тут
    if text == HISTORY_BY_DATE_BUTTON:
        update.message.reply_text("Выбери дату 👇", reply_markup=get_date_choose_keyboard())
        return HISTORY_DATE_CHOOSE

    user = get_or_create_tg_user(update)
    today = user_local_date(user)

    if text == "Сегодня":
        return history_show_by_date(update, context, today)
    if text == "Вчера":
        return history_show_by_date(update, context, today - timedelta(days=1))
    if text == "Позавчера":
        return history_show_by_date(update, context, today - timedelta(days=2))

    if text == "Ввести дату (ДД.ММ.ГГГГ)":
        update.message.reply_text(
            "Напиши дату в формате ДД.ММ.ГГГГ (например 25.12.2025).",
            reply_markup=get_date_input_keyboard(),
        )
        return HISTORY_DATE_INPUT

    # ✅ если пользователь ввёл дату вручную прямо в этом состоянии — принимаем
    picked = _parse_date_ddmmyyyy(text)
    if picked:
        return history_show_by_date(update, context, picked)

    update.message.reply_text("Не поняла выбор. Нажми кнопку 👇", reply_markup=get_date_choose_keyboard())
    return HISTORY_DATE_CHOOSE


def history_date_input(update: Update, context: CallbackContext):
    text = (update.message.text or "").strip()

    if text == BACK_BUTTON:
        return history_by_date_start(update, context)

    # на всякий: если в INPUT прилетели “Сегодня/Вчера/Позавчера”
    user = get_or_create_tg_user(update)
    today = user_local_date(user)
    if text == "Сегодня":
        return history_show_by_date(update, context, today)
    if text == "Вчера":
        return history_show_by_date(update, context, today - timedelta(days=1))
    if text == "Позавчера":
        return history_show_by_date(update, context, today - timedelta(days=2))

    picked = _parse_date_ddmmyyyy(text)
    if not picked:
        update.message.reply_text("Не похоже на дату. Пример: 25.12.2025", reply_markup=get_date_input_keyboard())
        return HISTORY_DATE_INPUT

    return history_show_by_date(update, context, picked)


# ---------- progress ----------
def history_progress(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    today = user_local_date(user)

    start = today - timedelta(days=13)
    entries = (
        DailyEntry.objects.filter(user=user, date__gte=start, date__lte=today)
        .order_by("date")
    )
    filled_days = sum(1 for e in entries if e.completed_morning or e.completed_evening)

    cycles = (
        WeeklyCycle.objects.filter(user=user, week_start__gte=today - timedelta(weeks=8))
        .order_by("-week_start")
    )
    completed_weeks = sum(1 for c in cycles if c.is_completed)

    update.message.reply_text(
        "📈 Прогресс\n\n"
        f"• Заполненных дней за последние 14 дней: {filled_days}/14\n"
        f"• Завершённых недель за последние 8 недель: {completed_weeks}/{cycles.count()}\n",
        reply_markup=get_history_menu_keyboard(),
    )
    return HISTORY_MENU


# ---------- search ----------
def history_search_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🔎 Напиши слово/фразу для поиска по ответам.\n"
        'Например: “мама”, “работа”, “страх”, “море”.',
        reply_markup=get_date_input_keyboard(),
    )
    return HISTORY_SEARCH_INPUT


def history_search_input(update: Update, context: CallbackContext):
    text = (update.message.text or "").strip()

    if text == BACK_BUTTON:
        return history_menu(update, context)

    if not text:
        update.message.reply_text("Напиши слово/фразу 🙂", reply_markup=get_date_input_keyboard())
        return HISTORY_SEARCH_INPUT

    user = get_or_create_tg_user(update)

    answers = (
        Answer.objects.filter(daily_entry__user=user)
        .filter(Q(answer_text__icontains=text) | Q(question_text__icontains=text))
        .select_related("daily_entry", "question")
        .order_by("-daily_entry__date", "-created_at")[:10]
    )

    if not answers:
        update.message.reply_text(f'Ничего не нашла по запросу: “{text}”.', reply_markup=get_history_menu_keyboard())
        return HISTORY_MENU

    lines = [f'🔎 Результаты по запросу: “{text}” (последние 10)\n']
    for a in answers:
        d = a.daily_entry.date
        q = _clean_question_text(a.question_text)
        ans = (a.answer_text or "").strip() or "—"
        lines.append(f"• {d:%d.%m.%Y}\n  ❓ {q}\n  → {ans}")

    update.message.reply_text("\n".join(lines), reply_markup=get_history_menu_keyboard())
    return HISTORY_MENU


# ---------- formatting helpers ----------
def _format_daily_entry(entry: DailyEntry) -> str:
    answers = (
        Answer.objects.filter(daily_entry=entry)
        .select_related("question")
        .order_by("created_at")
    )

    if not answers:
        return "Записей нет."

    morning: list[Answer] = []
    evening: list[Answer] = []
    other: list[Answer] = []

    for a in answers:
        p = _infer_period(a)
        if p == QuestionTemplate.PERIOD_MORNING:
            morning.append(a)
        elif p == QuestionTemplate.PERIOD_EVENING:
            evening.append(a)
        else:
            other.append(a)

    blocks = [
        _format_answers_block("☀️ Утро:", morning),
        _format_answers_block("🌙 Вечер:", evening),
        _format_answers_block("📝 Другое:", other),
    ]
    return "\n\n".join([b for b in blocks if b])


def _format_weekly_cycle(cycle: WeeklyCycle) -> str:
    header = f"🗓️ Неделя: {cycle.week_start:%d.%m} — {cycle.week_end:%d.%m}"

    task_text = ""
    if cycle.task and getattr(cycle.task, "is_active", True):
        task_text = f"\n🎯 Задание недели: {cycle.task.title}\n{cycle.task.description}"

    mid = (cycle.mid_reflection or "").strip() or "—"
    fin = (cycle.final_reflection or "").strip() or "—"

    return (
        header
        + task_text
        + "\n\n🧩 Промежуточный итог:\n" + mid
        + "\n\n🏁 Итог недели:\n" + fin
    )
