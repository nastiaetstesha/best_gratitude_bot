from django.utils import timezone
from datetime import date, timedelta
from core.models import TelegramUser, DailyEntry, QuestionTemplate, UserSettings, WeeklyCycle, WeeklyTask



def get_or_create_today_entry(user):
    today = timezone.localdate()
    entry, _ = DailyEntry.objects.get_or_create(user=user, date=today)
    return entry



def ensure_default_morning_questions():
    """
    Чтобы бот работал из коробки, даже если ты не заполнила QuestionTemplate в админке.
    Мы создаём дефолтные вопросы, если их нет.
    """
    if QuestionTemplate.objects.filter(period=QuestionTemplate.PERIOD_MORNING).exists():
        return

    defaults = [
        ("intention", "☀️ Утро\n\n1) Какое намерение/фокус ты выбираешь на сегодня?", 1),
        ("affirmation", "2) Положительная установка на день (1 фраза).", 2),
        ("one_step", "3) Один маленький шаг, который точно сделаешь сегодня?", 3),
    ]
    for code, text, order in defaults:
        QuestionTemplate.objects.create(
            code=f"morning_{code}",
            text=text,
            period=QuestionTemplate.PERIOD_MORNING,
            order=order,
            is_active=True,
        )


def get_morning_questions():
    ensure_default_morning_questions()
    return list(
        QuestionTemplate.objects.filter(
            period=QuestionTemplate.PERIOD_MORNING,
            is_active=True,
        ).order_by("order")
    )




def get_or_create_tg_user(update):
    tg = update.effective_user
    user, _ = TelegramUser.objects.get_or_create(
        telegram_id=tg.id,
        defaults={
            "username": tg.username,
            "first_name": tg.first_name,
            "last_name": tg.last_name,
        },
    )
    # обновим данные, если поменялись
    changed = False
    if user.username != tg.username:
        user.username = tg.username
        changed = True
    if user.first_name != tg.first_name:
        user.first_name = tg.first_name
        changed = True
    if user.last_name != tg.last_name:
        user.last_name = tg.last_name
        changed = True
    if changed:
        user.save(update_fields=["username", "first_name", "last_name"])
    return user


def get_user_settings(user: TelegramUser) -> UserSettings:
    settings, _ = UserSettings.objects.get_or_create(user=user)
    return settings

def get_iso_year_week(d: date) -> tuple[int, int]:
    iso = d.isocalendar()  # (year, week, weekday)
    return iso[0], iso[1]


def get_task_for_cycle(cycle: WeeklyCycle) -> WeeklyTask | None:
    iso_year, iso_week = get_iso_year_week(cycle.week_start)
    return (
        WeeklyTask.objects
        .filter(iso_year=iso_year, iso_week=iso_week, is_active=True)
        .first()
    )


def get_week_bounds(today: date, week_start_iso: int) -> tuple[date, date]:
    """
    week_start_iso: 1=Mon .. 7=Sun (как у тебя в UserSettings.week_start)
    """
    # date.isoweekday(): 1..7
    delta = (today.isoweekday() - week_start_iso) % 7
    start = today - timedelta(days=delta)
    end = start + timedelta(days=6)
    return start, end

def get_week_start_for_user(today: date, week_start_iso: int) -> date:
    """
    week_start_iso: 1=Mon ... 7=Sun (как у тебя в настройках).
    Возвращает дату начала "пользовательской недели".
    """
    # today.isoweekday(): 1..7
    delta = (today.isoweekday() - week_start_iso) % 7
    return today - timedelta(days=delta)


def get_or_create_current_week_cycle(user, today: date | None = None) -> WeeklyCycle:
    """
    Создаёт/возвращает WeeklyCycle для текущей недели пользователя.
    При создании сразу прикрепляет WeeklyTask по iso_year/iso_week.
    """
    if today is None:
        today = date.today()

    week_start_iso = user.settings.week_start if hasattr(user, "settings") else 1
    week_start = get_week_start_for_user(today, week_start_iso)
    week_end = week_start + timedelta(days=6)

    cycle, created = WeeklyCycle.objects.get_or_create(
        user=user,
        week_start=week_start,
        defaults={
            "week_end": week_end,
        },
    )

    # если цикл только что создали — подцепим задание недели
    if created or cycle.task_id is None:
        iso_year, iso_week = week_start.isocalendar()[0], week_start.isocalendar()[1]
        task = WeeklyTask.objects.filter(
            iso_year=iso_year,
            iso_week=iso_week,
            is_active=True,
        ).first()

        if task and cycle.task_id != task.id:
            cycle.task = task
            cycle.week_end = week_end  # на всякий случай поддержим актуальность
            cycle.save(update_fields=["task", "week_end"])

    return cycle
# def get_or_create_current_week_cycle(user: TelegramUser) -> WeeklyCycle:
#     settings = get_user_settings(user)
#     start, end = get_week_bounds(date.today(), settings.week_start)

#     cycle, _ = WeeklyCycle.objects.get_or_create(
#         user=user,
#         week_start=start,
#         defaults={"week_end": end},
#     )
#     # если week_end вдруг не совпал (на всякий случай)
#     if cycle.week_end != end:
#         cycle.week_end = end
#         cycle.save(update_fields=["week_end"])
#     return cycle


# def get_active_week_task() -> WeeklyTask | None:
#     return WeeklyTask.objects.filter(is_active=True).order_by("-created_at").first()
