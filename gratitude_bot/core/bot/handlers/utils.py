from datetime import date, timedelta

from django.utils import timezone

from core.models import (
    TelegramUser, DailyEntry, QuestionTemplate, UserSettings,
    WeeklyCycle, WeeklyTask,
)


def get_or_create_tg_user(update) -> TelegramUser:
    tg = update.effective_user
    user, _ = TelegramUser.objects.get_or_create(
        telegram_id=tg.id,
        defaults={
            "username": tg.username,
            "first_name": tg.first_name,
            "last_name": tg.last_name,
        },
    )

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

    # гарантируем настройки
    UserSettings.objects.get_or_create(user=user)

    return user


def get_user_settings(user: TelegramUser) -> UserSettings:
    settings, _ = UserSettings.objects.get_or_create(user=user)
    return settings


def get_or_create_today_entry(user: TelegramUser) -> DailyEntry:
    today = timezone.localdate()
    entry, _ = DailyEntry.objects.get_or_create(user=user, date=today)
    return entry


def ensure_default_morning_questions():
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


def get_week_start_for_user(today: date, week_start_iso: int) -> date:
    delta = (today.isoweekday() - week_start_iso) % 7
    return today - timedelta(days=delta)


def get_or_create_current_week_cycle(user: TelegramUser, today: date | None = None) -> WeeklyCycle:
    if today is None:
        today = date.today()

    settings = get_user_settings(user)
    week_start = get_week_start_for_user(today, settings.week_start)
    week_end = week_start + timedelta(days=6)

    cycle, created = WeeklyCycle.objects.get_or_create(
        user=user,
        week_start=week_start,
        defaults={"week_end": week_end},
    )

    # поддержим актуальный week_end
    if cycle.week_end != week_end:
        cycle.week_end = week_end
        cycle.save(update_fields=["week_end"])

    # подцепим задание по iso_year/iso_week
    if created or cycle.task_id is None:
        iso_year, iso_week = week_start.isocalendar()[0], week_start.isocalendar()[1]
        task = WeeklyTask.objects.filter(
            iso_year=iso_year,
            iso_week=iso_week,
            is_active=True,
        ).first()
        if task and cycle.task_id != task.id:
            cycle.task = task
            cycle.save(update_fields=["task"])

    return cycle
