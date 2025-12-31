# gratitude_bot/core/models.py
from datetime import time

from django.db import models


class TelegramUser(models.Model):
    """
    Пользователь бота (привязка к Telegram).
    Тут нет пароля и логина, всё определяется по telegram_id.
    """
    telegram_id = models.BigIntegerField(
        "Telegram ID",
        unique=True,
        db_index=True,
    )
    username = models.CharField(
        "Username",
        max_length=255,
        blank=True,
        null=True,
    )
    first_name = models.CharField(
        "Имя",
        max_length=255,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=255,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        "Дата регистрации в боте",
        auto_now_add=True,
    )

    def __str__(self):
        return self.username or f"user_{self.telegram_id}"


class UserSettings(models.Model):
    """
    Настройки напоминаний и поведения бота для конкретного пользователя.
    """
    user = models.OneToOneField(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="settings",
        verbose_name="Пользователь",
    )

    timezone = models.CharField(
        "Часовой пояс",
        max_length=64,
        default="Europe/Moscow",
        help_text="Строка часового пояса, например Europe/Moscow или Europe/Athens.",
    )

    morning_enabled = models.BooleanField(
        "Утренние вопросы включены",
        default=True,
    )
    evening_enabled = models.BooleanField(
        "Вечерние вопросы включены",
        default=True,
    )

    morning_time = models.TimeField(
        "Время утреннего напоминания",
        default=time(8, 0),
    )
    evening_time = models.TimeField(
        "Время вечернего напоминания",
        default=time(21, 0),
    )

    week_start = models.IntegerField(
        "День начала недели",
        default=1,
        help_text="1 = Понедельник, 7 = Воскресенье (ISO).",
    )

    notify_missed_days = models.BooleanField(
        "Напоминать о пропусках",
        default=True,
    )

    def __str__(self):
        return f"Настройки {self.user}"


class DailyEntry(models.Model):
    """
    Дневная запись: всё, что пользователь написал за конкретный день.
    Одна запись на пользователя + дату.
    """
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="daily_entries",
        verbose_name="Пользователь",
    )
    date = models.DateField(
        "Дата",
        db_index=True,
    )

    completed_morning = models.BooleanField(
        "Утренний блок заполнен",
        default=False,
    )
    completed_evening = models.BooleanField(
        "Вечерний блок заполнен",
        default=False,
    )

    # Необязательное поле – можно использовать для “мood трекера”
    mood = models.PositiveSmallIntegerField(
        "Настроение (1-5)",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        "Создано",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Обновлено",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Дневная запись"
        verbose_name_plural = "Дневные записи"
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} — {self.date}"


class QuestionTemplate(models.Model):
    """
    Шаблон вопроса (чтобы не хардкодить вопросы в коде).
    Например:
      code='gratitude_1', period='evening', text='Я благодарю за то, что...'
    """
    PERIOD_MORNING = "morning"
    PERIOD_EVENING = "evening"
    PERIOD_WEEKLY = "weekly"

    PERIOD_CHOICES = [
        (PERIOD_MORNING, "Утро"),
        (PERIOD_EVENING, "Вечер"),
        (PERIOD_WEEKLY, "Недельный вопрос"),
    ]

    code = models.CharField(
        "Код вопроса",
        max_length=50,
        unique=True,
        help_text="Внутренний идентификатор, по которому бот понимает, какой это вопрос.",
    )
    text = models.TextField(
        "Текст вопроса",
    )
    period = models.CharField(
        "Период",
        max_length=20,
        choices=PERIOD_CHOICES,
        default=PERIOD_EVENING,
        db_index=True,
    )
    order = models.PositiveSmallIntegerField(
        "Порядок в блоке",
        default=1,
        help_text="Определяет порядок вопросов утром/вечером.",
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
    )

    class Meta:
        verbose_name = "Шаблон вопроса"
        verbose_name_plural = "Шаблоны вопросов"
        ordering = ["period", "order"]

    def __str__(self):
        return f"[{self.period}] {self.text[:30]}..."


class Answer(models.Model):
    """
    Конкретный ответ пользователя на конкретный вопрос в рамках одного дня.
    """
    daily_entry = models.ForeignKey(
        DailyEntry,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Дневная запись",
    )
    question = models.ForeignKey(
        QuestionTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="answers",
        verbose_name="Шаблон вопроса",
        help_text="Может быть null, если вопрос потом удалили или изменили.",
    )
    # Дублируем текст вопроса на момент ответа, чтобы история не ломалась, если вопрос изменят
    question_text = models.TextField(
        "Текст вопроса в момент ответа",
    )
    answer_text = models.TextField(
        "Ответ пользователя",
    )
    created_at = models.DateTimeField(
        "Дата и время ответа",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.daily_entry} — {self.question_text[:30]}..."


class WeeklyTask(models.Model):
    """
    Задание недели (как в твоем дневнике).
    """
    title = models.CharField(
        "Название задания",
        max_length=255,
    )
    description = models.TextField(
        "Описание задания",
    )
    is_active = models.BooleanField(
        "Показывать пользователям",
        default=True,
    )
    created_at = models.DateTimeField(
        "Создано",
        auto_now_add=True,
    )
    iso_year = models.IntegerField(db_index=True)   # год ISO-недели
    iso_week = models.IntegerField(db_index=True)   # номер ISO-недели 1..53

    class Meta:
        verbose_name = "Задание недели"
        verbose_name_plural = "Задания недели"
        unique_together = ("iso_year", "iso_week")

    def __str__(self):
        return self.title


class WeeklyCycle(models.Model):
    """
    Конкретная 'неделя' пользователя: какое задание он получил и когда.
    Здесь можно хранить промежуточный и финальный итоги недели.
    """
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="weekly_cycles",
        verbose_name="Пользователь",
    )
    task = models.ForeignKey(
        WeeklyTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_cycles",
        verbose_name="Задание недели",
    )
    week_start = models.DateField(
        "Начало недели",
        db_index=True,
    )
    week_end = models.DateField(
        "Конец недели",
        db_index=True,
    )

    # Можно хранить текстовые итоги:
    mid_reflection = models.TextField(
        "Промежуточный итог",
        blank=True,
    )
    final_reflection = models.TextField(
        "Итог недели",
        blank=True,
    )

    is_completed = models.BooleanField(
        "Неделя завершена",
        default=False,
    )

    created_at = models.DateTimeField(
        "Создано",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Недельный цикл"
        verbose_name_plural = "Недельные циклы"
        unique_together = ("user", "week_start")
        ordering = ["-week_start"]

    def __str__(self):
        return f"{self.user} — неделя с {self.week_start}"


class NudgePhrase(models.Model):
    """
    Фразы-напоминания, чтобы спасти стрик или мягко вернуть пользователя.
    """
    CATEGORY_STREAK = "streak"
    CATEGORY_COMEBACK = "comeback"

    CATEGORY_CHOICES = [
        (CATEGORY_STREAK, "Сохранить стрик"),
        (CATEGORY_COMEBACK, "Вернуться после перерыва"),
    ]

    text = models.CharField(
        "Текст фразы",
        max_length=255,
    )
    category = models.CharField(
        "Категория",
        max_length=32,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_STREAK,
        db_index=True,
    )
    is_active = models.BooleanField(
        "Активна",
        default=True,
    )

    class Meta:
        verbose_name = "Фраза напоминания"
        verbose_name_plural = "Фразы напоминаний"

    def __str__(self):
        return f"[{self.category}] {self.text}"


class StreakState(models.Model):
    """
    Состояние стрика пользователя.
    Чтобы не пересчитывать каждый раз — храним текущее значение и лучший рекорд.
    """
    user = models.OneToOneField(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="streak_state",
        verbose_name="Пользователь",
    )
    current_streak = models.PositiveIntegerField(
        "Текущий стрик (в днях)",
        default=0,
    )
    best_streak = models.PositiveIntegerField(
        "Лучший стрик (в днях)",
        default=0,
    )
    last_completed_date = models.DateField(
        "Дата последнего полностью заполненного дня",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = "Стрик пользователя"
        verbose_name_plural = "Стрики пользователей"

    def __str__(self):
        return f"{self.user}: {self.current_streak} дней"
