from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from core.bot.handlers.utils import (
    get_or_create_tg_user,
    get_or_create_today_entry,
    get_morning_questions,
)
from core.bot.keyboards.main_menu import (
    get_cancel_keyboard,
    get_main_menu_keyboard,
    get_morning_completed_keyboard,
    BACK_BUTTON,
)
from core.models import Answer, DailyEntry


# Состояние одно: мы всегда принимаем текст и двигаем шаги сами
MORNING_ANSWER = 1

# Кнопки
MORNING_REDO_BUTTON = "Заполнить утро заново"
VIEW_TODAY_ANSWERS = "Посмотреть сегодняшние ответы"


def morning_start(update: Update, context: CallbackContext):
    """
    Запуск утреннего опросника из:
    - главного меню "Утро"
    - меню Сегодня "Заполнить утро"
    """
    user = get_or_create_tg_user(update)
    entry = get_or_create_today_entry(user)

    # Если уже заполнено — не запускаем заново без явного выбора
    if entry.completed_morning:
        update.message.reply_text(
            "☀️ Утро на сегодня уже заполнено ✅\n\n"
            "Хочешь посмотреть ответы или заполнить заново?",
            reply_markup=get_morning_completed_keyboard(),
        )
        return ConversationHandler.END

    questions = get_morning_questions()

    context.user_data["morning_entry_id"] = entry.id
    context.user_data["morning_q_ids"] = [q.id for q in questions]
    context.user_data["morning_step"] = 0

    update.message.reply_text(
        "☀️ Утренний блок — 2 минуты.\n"
        "Если захочешь выйти — нажми «Назад».",
        reply_markup=get_cancel_keyboard(),
    )

    # первый вопрос
    update.message.reply_text(questions[0].text)
    return MORNING_ANSWER


def morning_handle_answer(update: Update, context: CallbackContext):
    entry_id = context.user_data.get("morning_entry_id")
    q_ids = context.user_data.get("morning_q_ids")
    step = context.user_data.get("morning_step", 0)

    if not entry_id or not q_ids:
        update.message.reply_text(
            "Похоже, сессия утра потерялась. Нажми «Утро», чтобы начать заново.",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    text = (update.message.text or "").strip()
    if not text:
        update.message.reply_text("Можно коротко, но не пусто 🙂")
        return MORNING_ANSWER

    # сохраняем ответ на текущий вопрос
    question_id = q_ids[step]

    # чтобы корректно сохранять question_text даже если потом поменяют шаблон
    from core.models import QuestionTemplate
    q = QuestionTemplate.objects.get(id=question_id)

    Answer.objects.create(
        daily_entry_id=entry_id,
        question=q,
        question_text=q.text,
        answer_text=text,
    )

    step += 1
    context.user_data["morning_step"] = step

    # конец опросника
    if step >= len(q_ids):
        DailyEntry.objects.filter(id=entry_id).update(completed_morning=True)

        # чистим user_data
        _clear_morning_context(context)

        update.message.reply_text(
            "✅ Утро заполнено. Хорошего дня 🌿",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    # следующий вопрос
    from core.models import QuestionTemplate
    next_q = QuestionTemplate.objects.get(id=q_ids[step])
    update.message.reply_text(next_q.text)
    return MORNING_ANSWER


def morning_cancel(update: Update, context: CallbackContext):
    _clear_morning_context(context)
    update.message.reply_text(
        "Ок, верну в меню 👇",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


def morning_redo(update: Update, context: CallbackContext):
    """
    Пользователь нажал "Заполнить утро заново".
    Мы удаляем утренние ответы за сегодня и запускаем опросник.
    """
    user = get_or_create_tg_user(update)
    entry = get_or_create_today_entry(user)

    # удаляем только утренние ответы: по question.period == morning
    Answer.objects.filter(
        daily_entry=entry,
        question__period="morning",
    ).delete()

    # На всякий случай удалим и те ответы, где question мог стать null, но это утро:
    # (если ты когда-то удалишь QuestionTemplate — связь станет null)
    # Мы определим "утро" по префиксу в question_text (у нас первый вопрос начинается с ☀️ Утро)
    Answer.objects.filter(
        daily_entry=entry,
        question__isnull=True,
        question_text__icontains="утро",
    ).delete()

    DailyEntry.objects.filter(id=entry.id).update(completed_morning=False)

    update.message.reply_text("Ок, заполним заново ☀️")
    return morning_start(update, context)


def view_today_answers(update: Update, context: CallbackContext):
    """
    Выводим сегодняшние ответы (утро+вечер), но начнём с утра — как ты просила.
    """
    user = get_or_create_tg_user(update)
    entry = get_or_create_today_entry(user)

    answers = Answer.objects.filter(daily_entry=entry).order_by("created_at")
    if not answers.exists():
        update.message.reply_text(
            "Сегодня пока нет ответов.\nНажми «Заполнить утро» или «Заполнить вечер».",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # сгруппируем простенько: утро / вечер / прочее
    morning = []
    evening = []
    other = []

    for a in answers:
        period = getattr(a.question, "period", None)
        if period == "morning":
            morning.append(a)
        elif period == "evening":
            evening.append(a)
        else:
            other.append(a)

    parts = []
    if morning:
        parts.append("☀️ Утро:")
        for i, a in enumerate(morning, 1):
            parts.append(f"{i}) {a.answer_text}")
    if evening:
        parts.append("\n🌙 Вечер:")
        for i, a in enumerate(evening, 1):
            parts.append(f"{i}) {a.answer_text}")
    if other:
        parts.append("\n📝 Другое:")
        for i, a in enumerate(other, 1):
            parts.append(f"{i}) {a.answer_text}")

    update.message.reply_text(
        "\n".join(parts),
        reply_markup=get_main_menu_keyboard(),
    )


def _clear_morning_context(context: CallbackContext):
    context.user_data.pop("morning_entry_id", None)
    context.user_data.pop("morning_q_ids", None)
    context.user_data.pop("morning_step", None)
