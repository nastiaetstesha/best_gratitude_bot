# gratitude_bot/core/bot/handlers/evening_flow.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from core.bot.keyboards.main_menu import (
    BACK_BUTTON,
    get_cancel_keyboard,
    get_main_menu_keyboard,
)
from core.bot.handlers.utils import get_or_create_tg_user, get_or_create_today_entry
from core.services.streak import update_streak_on_activity
from core.models import Answer, DailyEntry


# Состояния (int)
EV_GRAT_1, EV_GRAT_2, EV_GRAT_3, EV_BEST = range(4)

EVENING_REDO_BUTTON = "Заполнить вечер заново"
VIEW_TODAY_ANSWERS = "Посмотреть сегодняшние ответы"

EVENING_QUESTIONS = [
    ("gratitude_1", "🌙 Вечер\n\n1) За что ты сегодня благодарна?"),
    ("gratitude_2", "2) Прекрасные моменты дня сегодня — какие они?"),
    ("gratitude_3", "3) Что я смогу сделать завтра, чтобы сделать свой день лучше?"),
    ("best_event", "✨ Что было самым хорошим/тёплым событием дня?"),
]


def get_evening_completed_keyboard():
    return ReplyKeyboardMarkup(
        [
            [VIEW_TODAY_ANSWERS],
            [EVENING_REDO_BUTTON],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def evening_start(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    entry = get_or_create_today_entry(user)

    if entry.completed_evening:
        update.message.reply_text(
            "🌙 Вечер на сегодня уже заполнен ✅\n\n"
            "Хочешь посмотреть ответы или заполнить заново?",
            reply_markup=get_evening_completed_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["evening_entry_id"] = entry.id
    context.user_data["evening_step"] = 0

    update.message.reply_text(
        "🌙 Вечерняя рефлексия займёт 2–3 минуты.\n\n"
        "Если захочешь выйти — нажми «Назад».",
        reply_markup=get_cancel_keyboard(),
    )

    _, text = EVENING_QUESTIONS[0]
    update.message.reply_text(text)
    return EV_GRAT_1


def _save_answer(entry_id: int, question_text: str, answer_text: str):
    Answer.objects.create(
        daily_entry_id=entry_id,
        question=None,  # вечер сейчас сохраняется без QuestionTemplate
        question_text=question_text,
        answer_text=answer_text.strip(),
    )


def _state_by_step(step: int):
    if step == 0:
        return EV_GRAT_1
    if step == 1:
        return EV_GRAT_2
    if step == 2:
        return EV_GRAT_3
    return EV_BEST


def evening_handle_answer(update: Update, context: CallbackContext):
    entry_id = context.user_data.get("evening_entry_id")
    step = context.user_data.get("evening_step", 0)

    if not entry_id:
        update.message.reply_text(
            "Похоже, сессия вечера потерялась. Нажми «Вечер», чтобы начать заново.",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    user_text = (update.message.text or "").strip()
    if not user_text:
        update.message.reply_text("Можно коротко, но не пусто 🙂")
        return _state_by_step(step)

    # сохраняем текущий ответ
    _, q_text = EVENING_QUESTIONS[step]
    _save_answer(entry_id, q_text, user_text)

    step += 1
    context.user_data["evening_step"] = step

    if step >= len(EVENING_QUESTIONS):
        DailyEntry.objects.filter(id=entry_id).update(completed_evening=True)

        # ✅ стрик
        entry = DailyEntry.objects.get(id=entry_id)
        user = entry.user
        update_streak_on_activity(user, entry.date)

        _clear_evening_context(context)

        update.message.reply_text(
            "✅ Вечер заполнен. Спасибо 🌙",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    _, next_text = EVENING_QUESTIONS[step]
    update.message.reply_text(next_text)
    return _state_by_step(step)


def evening_redo(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    entry = get_or_create_today_entry(user)

    evening_texts = [q[1] for q in EVENING_QUESTIONS]
    Answer.objects.filter(daily_entry=entry, question_text__in=evening_texts).delete()

    DailyEntry.objects.filter(id=entry.id).update(completed_evening=False)

    update.message.reply_text("Ок, заполним заново 🌙")
    return evening_start(update, context)


def evening_cancel(update: Update, context: CallbackContext):
    _clear_evening_context(context)
    update.message.reply_text("Ок, верну в меню 👇", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


def view_today_answers(update: Update, context: CallbackContext):
    """
    Показываем сегодняшние ответы (утро/вечер/другое) с вопросами:
    ❓ question_text
    → answer_text
    """
    user = get_or_create_tg_user(update)
    entry = get_or_create_today_entry(user)

    answers = Answer.objects.filter(daily_entry=entry).order_by("created_at")
    if not answers.exists():
        update.message.reply_text(
            "Сегодня пока нет ответов.\nНажми «Заполнить утро» или «Заполнить вечер».",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    # Вечерные тексты — чтобы отличать вечер от "другое"
    evening_texts = {q[1] for q in EVENING_QUESTIONS}

    morning, evening, other = [], [], []

    for a in answers:
        period = getattr(a.question, "period", None)
        if period == "morning":
            morning.append(a)
            continue

        # вечер: либо period=evening, либо совпало по тексту вопроса
        if period == "evening" or (a.question_text in evening_texts):
            evening.append(a)
        else:
            other.append(a)

    parts = [f"📅 {entry.date:%d.%m.%Y}\n"]

    if morning:
        parts.append("☀️ Утро:")
        for a in morning:
            parts.append(f"❓ {a.question_text}\n→ {a.answer_text}")

    if evening:
        parts.append("\n🌙 Вечер:")
        for a in evening:
            parts.append(f"❓ {a.question_text}\n→ {a.answer_text}")

    if other:
        parts.append("\n📝 Другое:")
        for a in other:
            parts.append(f"❓ {a.question_text}\n→ {a.answer_text}")

    update.message.reply_text("\n".join(parts), reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


def _clear_evening_context(context: CallbackContext):
    context.user_data.pop("evening_entry_id", None)
    context.user_data.pop("evening_step", None)
