from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler

from core.bot.keyboards.main_menu import get_cancel_keyboard, get_main_menu_keyboard, BACK_BUTTON
from core.bot.handlers.utils import get_or_create_tg_user, get_or_create_today_entry
from core.models import Answer


# Состояния (int)
EV_GRAT_1, EV_GRAT_2, EV_GRAT_3, EV_BEST, EV_DONE = range(5)


EVENING_QUESTIONS = [
    ("gratitude_1", "🌙 Вечер\n\n1) За что ты сегодня благодарна?"),
    ("gratitude_2", "2) Прекрасные моменты дня сегодня — какие они?"),
    ("gratitude_3", "3) Что я смогу сделать завтра, чтобы сделать свой день лучше?"),
    ("best_event", "✨ Что было самым хорошим/тёплым событием дня?"),
]


def evening_start(update: Update, context: CallbackContext):
    """
    Вход в вечерний опросник
    """
    user = get_or_create_tg_user(update)
    entry = get_or_create_today_entry(user)

    context.user_data["entry_id"] = entry.id
    context.user_data["evening_step"] = 0

    update.message.reply_text(
        "🌙 Вечерняя рефлексия займёт 2–3 минуты.\n\n"
        "Если захочешь выйти — нажми «Назад».",
        reply_markup=get_cancel_keyboard(),
    )

    # задаём первый вопрос
    code, text = EVENING_QUESTIONS[0]
    update.message.reply_text(text)
    return EV_GRAT_1


def _save_answer(entry_id: int, question_code: str, question_text: str, answer_text: str):
    Answer.objects.create(
        daily_entry_id=entry_id,
        question=None,
        question_text=question_text,
        answer_text=answer_text.strip(),
    )


def evening_handle_answer(update: Update, context: CallbackContext):
    """
    Универсальный обработчик ответа на текущий вопрос
    """
    entry_id = context.user_data.get("entry_id")
    step = context.user_data.get("evening_step", 0)

    if not entry_id:
        update.message.reply_text("Что-то пошло не так. Давай начнём заново.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    user_text = (update.message.text or "").strip()
    if not user_text:
        update.message.reply_text("Можно коротко, но не пусто 🙂")
        return _state_by_step(step)

    # сохраняем текущий ответ
    q_code, q_text = EVENING_QUESTIONS[step]
    _save_answer(entry_id, q_code, q_text, user_text)

    step += 1
    context.user_data["evening_step"] = step

    # если вопросы закончились — завершаем
    if step >= len(EVENING_QUESTIONS):
        from core.models import DailyEntry
        DailyEntry.objects.filter(id=entry_id).update(completed_evening=True)

        update.message.reply_text(
            "✅ Готово! Спасибо.\n\n"
            "Хочешь — можешь потом посмотреть ответы в «Сегодня» или в «История».",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    # иначе задаём следующий
    _, next_text = EVENING_QUESTIONS[step]
    update.message.reply_text(next_text)
    return _state_by_step(step)


def _state_by_step(step: int):
    """
    сопоставляем step -> state
    """
    if step == 0:
        return EV_GRAT_1
    if step == 1:
        return EV_GRAT_2
    if step == 2:
        return EV_GRAT_3
    return EV_BEST


def evening_cancel(update: Update, context: CallbackContext):
    """
    Отмена/выход по кнопке Назад
    """
    context.user_data.pop("entry_id", None)
    context.user_data.pop("evening_step", None)

    update.message.reply_text(
        "Ок, верну в меню 👇",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END
