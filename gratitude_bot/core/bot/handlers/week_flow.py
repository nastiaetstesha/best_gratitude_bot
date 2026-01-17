from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from telegram.utils.helpers import escape_markdown


from core.bot.handlers.utils import (
    get_or_create_tg_user,
    get_or_create_current_week_cycle,
    user_local_date,
)
from core.bot.keyboards.main_menu import (
    get_main_menu_keyboard,
    get_week_menu_keyboard,
    get_cancel_keyboard,
    BACK_BUTTON,
)
from core.models import WeeklyCycle
# from core.bot.handlers.utils import get_or_create_tg_user, get_or_create_current_week_cycle


WEEK_FILL_BUTTON = "Заполнить неделю"
WEEK_VIEW_BUTTON = "Посмотреть недельные ответы"
WEEK_TASK_BUTTON = "Задание недели"
WEEK_REDO_BUTTON = "Заполнить неделю заново"

# Состояния диалога "Заполнить неделю"
WEEK_MID = 201
WEEK_FINAL = 202


def week_menu(update: Update, context: CallbackContext):
    """
    Открывает меню недели (как на скрине).
    """
    update.message.reply_text(
        "Неделя 🗓️\nЧто делаем?",
        reply_markup=get_week_menu_keyboard(),
    )
    return ConversationHandler.END


def week_fill_start(update: Update, context: CallbackContext):
    """
    Старт заполнения недели. Спрашиваем mid_reflection, потом final_reflection.
    """
    user = get_or_create_tg_user(update)
    cycle = get_or_create_current_week_cycle(user, today=user_local_date(user))


    # если уже заполнено — предложим посмотреть/перезаполнить
    if cycle.is_completed:
        update.message.reply_text(
            f"Неделя уже заполнена ✅\n"
            f"Период: {cycle.week_start:%d.%m} — {cycle.week_end:%d.%m}\n\n"
            f"Хочешь посмотреть ответы или заполнить заново?",
            reply_markup=_get_week_completed_keyboard(),
        )
        return ConversationHandler.END

    # назначим задание недели (если есть активное)
    # task = get_active_week_task()
    # if task and cycle.task_id is None:
    #     cycle.task = task
    #     cycle.save(update_fields=["task"])

    context.user_data["week_cycle_id"] = cycle.id

    update.message.reply_text(
        f"❤️ Заполним неделю (2–3 минуты).\n"
        f"Если захочешь выйти — нажми «{BACK_BUTTON}».",
        reply_markup=get_cancel_keyboard(),
    )

    # Вопрос 1: mid_reflection
    update.message.reply_text(
        "1) Промежуточный итог недели:\n"
        "Что у тебя получилось? Какие маленькие победы были?"
    )
    return WEEK_MID


def week_handle_mid(update: Update, context: CallbackContext):
    if _is_back(update):
        return week_cancel(update, context)

    text = (update.message.text or "").strip()
    if not text:
        update.message.reply_text("Можно коротко, но не пусто 🙂")
        return WEEK_MID

    cycle = _get_cycle_from_context(update, context)
    if not cycle:
        return ConversationHandler.END

    cycle.mid_reflection = text
    cycle.save(update_fields=["mid_reflection"])

    update.message.reply_text(
        "2) Итог недели:\n"
        "Что было самым важным? Какие выводы берёшь в следующую неделю?"
    )
    return WEEK_FINAL


def week_handle_final(update: Update, context: CallbackContext):
    if _is_back(update):
        return week_cancel(update, context)

    text = (update.message.text or "").strip()
    if not text:
        update.message.reply_text("Можно коротко, но не пусто 🙂")
        return WEEK_FINAL

    cycle = _get_cycle_from_context(update, context)
    if not cycle:
        return ConversationHandler.END

    cycle.final_reflection = text
    cycle.is_completed = True
    cycle.save(update_fields=["final_reflection", "is_completed"])

    context.user_data.pop("week_cycle_id", None)

    update.message.reply_text(
        "✅ Неделя заполнена. Горжусь твоей устойчивостью 🌿",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


def week_cancel(update: Update, context: CallbackContext):
    context.user_data.pop("week_cycle_id", None)
    update.message.reply_text(
        "Ок, верну в меню 👇",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


def week_view(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    cycle = get_or_create_current_week_cycle(user, today=user_local_date(user))


    header = f"🗓️ Неделя: {cycle.week_start:%d.%m} — {cycle.week_end:%d.%m}\n"

    task_text = ""
    if cycle.task:
        task_text = (f"\n🎯 Задание недели: {cycle.task.title}\n{cycle.task.description}\n"
        # f"Выполни задание, нажав кнопку 'Заполнить неделю'.\n"
        # f"Это только описание задания - отвечать на сообщение не нужно\n"
        )

    mid = cycle.mid_reflection.strip() if (cycle.mid_reflection or "").strip() else "—"
    fin = cycle.final_reflection.strip() if (cycle.final_reflection or "").strip() else "—"

    update.message.reply_text(
        header
        + task_text
        + "\n🧩 Промежуточный итог:\n"
        + mid
        + "\n\n🏁 Итог недели:\n"
        + fin,
        reply_markup=get_main_menu_keyboard(),
    )


def week_menu(update: Update, context: CallbackContext):
    update.message.reply_text("Неделя 📆", reply_markup=get_week_menu_keyboard())

# !!!!!!!!!!

def week_task_show(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    cycle = get_or_create_current_week_cycle(user, today=user_local_date(user))


    if not cycle.task:
        update.message.reply_text(
            "На эту неделю пока нет задания 😅\n"
            "Добавь его в админке (WeeklyTask с iso_year/iso_week).",
            reply_markup=get_week_menu_keyboard(),
        )
        return

    title = escape_markdown(cycle.task.title, version=2)
    description = escape_markdown(cycle.task.description, version=2)
    update.message.reply_text(
        f"🎯 Задание недели\n\n"
        f"*{title}*\n\n"
        f"{description}\n\n"
        f"> Выполни задание, нажав кнопку 'Заполнить неделю'\\.\n"
        f"> Это только описание задания \\- отвечать на сообщение не нужно\n",
        reply_markup=get_week_menu_keyboard(),
        parse_mode="MarkdownV2",
    )

def week_redo(update: Update, context: CallbackContext):
    user = get_or_create_tg_user(update)
    cycle = get_or_create_current_week_cycle(user, today=user_local_date(user))


    cycle.mid_reflection = ""
    cycle.final_reflection = ""
    cycle.is_completed = False
    cycle.save(update_fields=["mid_reflection", "final_reflection", "is_completed"])

    update.message.reply_text("Ок, заполним заново ❤️")
    return week_fill_start(update, context)


def _get_week_completed_keyboard():
    from telegram import ReplyKeyboardMarkup
    return ReplyKeyboardMarkup(
        [
            [WEEK_VIEW_BUTTON],
            [WEEK_REDO_BUTTON],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _is_back(update: Update) -> bool:
    return (update.message.text or "").strip() == BACK_BUTTON


def _get_cycle_from_context(update: Update, context: CallbackContext) -> WeeklyCycle | None:
    cycle_id = context.user_data.get("week_cycle_id")
    if not cycle_id:
        update.message.reply_text(
            "Похоже, сессия недели потерялась. Нажми «Неделя», чтобы начать заново.",
            reply_markup=get_main_menu_keyboard(),
        )
        return None
    try:
        return WeeklyCycle.objects.get(id=cycle_id)
    except WeeklyCycle.DoesNotExist:
        update.message.reply_text(
            "Не найдена текущая неделя. Нажми «Неделя», чтобы начать заново.",
            reply_markup=get_main_menu_keyboard(),
        )
        return None
