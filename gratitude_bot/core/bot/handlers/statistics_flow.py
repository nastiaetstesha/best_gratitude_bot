# gratitude_bot/core/bot/handlers/statistics_flow.py

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from core.models import DailyEntry, Answer, WeeklyCycle, QuestionTemplate, StreakState
from core.bot.handlers.utils import get_or_create_tg_user, user_local_date
from core.bot.keyboards.main_menu import (
    BACK_BUTTON,
    get_main_menu_keyboard,
    get_statistics_menu_keyboard,
)

# ---------- buttons text-----
STATS_GENERAL_BUTTON = "Общая статистика"
STATS_CHART_BUTTON = "График заполнений"
STATS_TOPICS_BUTTON = "Частые темы благодарности"
STATS_WEEKDAYS_BUTTON = "Статистика по дням недели"

# ---------- states ----------
STATS_MENU = 401

_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё]+", re.UNICODE)

# Можно расширить,
RU_STOPWORDS = {
    "и", "а", "но", "или", "что", "это", "как", "я", "мы", "ты", "он", "она", "они",
    "в", "во", "на", "за", "к", "ко", "с", "со", "у", "о", "об", "от", "для", "по",
    "из", "до", "без", "при", "же", "ли", "бы", "то", "там", "тут", "здесь",
    "сегодня", "вчера", "завтра", "очень", "просто", "еще", "уже", "все", "всё",
    "мне", "меня", "мой", "моя", "мои", "тебя", "твой", "твоя", "его", "ее", "её",
    "быть", "была", "был", "были",
}

WEEKDAY_RU = {
    1: "Пн",
    2: "Вт",
    3: "Ср",
    4: "Чт",
    5: "Пт",
    6: "Сб",
    7: "Вс",
}


def statistics_menu(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Статистика 📊\nЧто посмотрим?",
        reply_markup=get_statistics_menu_keyboard(),
    )
    return STATS_MENU


def statistics_cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Ок, верну в меню 👇", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


# -------------------- handlers for menu buttons --------------------
def statistics_general(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    today = user_local_date(user)

    # За всё время
    all_entries = DailyEntry.objects.filter(user=user)
    total_days = all_entries.count()
    days_with_any = all_entries.filter(Q(completed_morning=True) | Q(completed_evening=True)).count()
    days_full = all_entries.filter(completed_morning=True, completed_evening=True).count()

    # Последние 30 дней
    since_30 = today - timedelta(days=29)
    last30 = all_entries.filter(date__gte=since_30, date__lte=today).order_by("date")
    last30_total = last30.count()
    last30_any = last30.filter(Q(completed_morning=True) | Q(completed_evening=True)).count()
    last30_full = last30.filter(completed_morning=True, completed_evening=True).count()

    # Недельные циклы
    cycles = WeeklyCycle.objects.filter(user=user)
    weeks_total = cycles.count()
    weeks_completed = cycles.filter(is_completed=True).count()

    # Стрик (если таблица есть)
    streak = StreakState.objects.filter(user=user).first()
    if streak:
        streak_line = f"🔥 Стрик: {streak.current_streak} (рекорд: {streak.best_streak})"
    else:
        streak_line = "🔥 Стрик: пока не считаем (таблица StreakState пустая)"

    msg = (
        "📊 Общая статистика\n\n"
        f"🗓️ За всё время:\n"
        f"• Дней в базе: {total_days}\n"
        f"• Дней с любым заполнением (утро или вечер): {days_with_any}\n"
        f"• Дней полностью (утро + вечер): {days_full}\n\n"
        f"🕒 Последние 30 дней:\n"
        f"• Дней: {last30_total}\n"
        f"• С заполнением: {last30_any}/30\n"
        f"• Полностью: {last30_full}/30\n\n"
        f"🗓️ Недели:\n"
        f"• Недель создано: {weeks_total}\n"
        f"• Недель завершено: {weeks_completed}\n\n"
        f"{streak_line}"
    )

    update.message.reply_text(msg, reply_markup=get_statistics_menu_keyboard())
    return STATS_MENU


def statistics_fill_chart(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    today = user_local_date(user)
    start = today - timedelta(days=13)

    entries = {
        e.date: e
        for e in DailyEntry.objects.filter(user=user, date__gte=start, date__lte=today)
    }

    lines = ["📈 График заполнений (последние 14 дней)\n"]
    for i in range(14):
        d = start + timedelta(days=i)
        e = entries.get(d)

        if not e:
            box = "⬜️"
        else:
            if e.completed_morning and e.completed_evening:
                box = "🟩"
            elif e.completed_morning or e.completed_evening:
                box = "🟨"
            else:
                box = "⬜️"

        # квадратик всегда в одной и той же позиции (в начале строки)
        lines.append(f"{box}  {d:%d.%m} {WEEKDAY_RU[d.isoweekday()]}")

    lines.append("\nОписание: ⬜️ нет, 🟨 частично, 🟩 полностью")

    update.message.reply_text(
        "\n".join(lines),
        reply_markup=get_statistics_menu_keyboard(),
    )
    return STATS_MENU




def statistics_weekdays(update: Update, context: CallbackContext):
    """
    Статистика по дням недели за последние 8 недель (56 дней):
    - сколько дней было
    - сколько заполнено частично/полностью
    """
    user = get_or_create_tg_user(update)
    today = user_local_date(user)
    start = today - timedelta(days=55)

    qs = DailyEntry.objects.filter(user=user, date__gte=start, date__lte=today)
    stats = {i: {"total": 0, "any": 0, "full": 0} for i in range(1, 8)}

    # посчитаем по календарным дням (даже если записи не создавались)
    for i in range(56):
        d = start + timedelta(days=i)
        wd = d.isoweekday()
        stats[wd]["total"] += 1

    # теперь наложим реальные заполнения
    for e in qs:
        wd = e.date.isoweekday()
        if e.completed_morning or e.completed_evening:
            stats[wd]["any"] += 1
        if e.completed_morning and e.completed_evening:
            stats[wd]["full"] += 1

    lines = ["📅 Статистика по дням недели (последние 8 недель)\n"]
    for wd in range(1, 8):
        t = stats[wd]["total"]
        any_ = stats[wd]["any"]
        full = stats[wd]["full"]
        # простая “полоска” из 10 символов по доле any
        filled = int(round((any_ / t) * 10)) if t else 0
        bar = "🟩" * filled + "⬜️" * (10 - filled)
        lines.append(f"{WEEKDAY_RU[wd]}  {bar}  заполнено: {any_}/{t}  полностью: {full}/{t}")

    update.message.reply_text("\n".join(lines), reply_markup=get_statistics_menu_keyboard())
    return STATS_MENU


def statistics_topics(update: Update, context: CallbackContext):
    """
    Частые темы благодарности:
    - берём ответы ВЕЧЕРА (period=evening)
    - вынимаем слова, фильтруем стоп-слова
    - показываем топ-10
    """
    user = get_or_create_tg_user(update)
    today = user_local_date(user)
    start = today - timedelta(days=30)  # последние 31 день

    answers = (
        Answer.objects
        .filter(daily_entry__user=user, daily_entry__date__gte=start, daily_entry__date__lte=today)
        .select_related("question", "daily_entry")
        .order_by("-created_at")
    )

    # отфильтруем вечерние ответы
    evening_answers = []
    for a in answers:
        period = getattr(a.question, "period", None)
        if period == QuestionTemplate.PERIOD_EVENING:
            evening_answers.append(a)
            continue
        # fallback: если вопрос удалили, попробуем по тексту
        qt = (a.question_text or "").lower()
        if "вечер" in qt or "🌙" in qt:
            evening_answers.append(a)

    if not evening_answers:
        update.message.reply_text(
            "Пока нет вечерних ответов за последние 30 дней.\n"
            "Заполни пару вечеров — и я покажу частые темы 🌙",
            reply_markup=get_statistics_menu_keyboard(),
        )
        return STATS_MENU

    counter = Counter()

    for a in evening_answers:
        text = (a.answer_text or "").lower()
        words = _WORD_RE.findall(text)
        for w in words:
            if len(w) < 3:
                continue
            if w in RU_STOPWORDS:
                continue
            counter[w] += 1

    if not counter:
        update.message.reply_text(
            "Не смогла выделить темы (слишком короткие ответы или только стоп-слова).",
            reply_markup=get_statistics_menu_keyboard(),
        )
        return STATS_MENU

    top = counter.most_common(10)
    lines = ["✨ Частые темы благодарности (по вечерним ответам, 30 дней)\n"]
    for i, (w, c) in enumerate(top, 1):
        lines.append(f"{i}) {w} — {c}")

    update.message.reply_text("\n".join(lines), reply_markup=get_statistics_menu_keyboard())
    return STATS_MENU
