from django.contrib import admin

from .models import (
    TelegramUser,
    UserSettings,
    DailyEntry,
    QuestionTemplate,
    Answer,
    WeeklyTask,
    WeeklyCycle,
    NudgePhrase,
    StreakState,
)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "first_name", "created_at")
    search_fields = ("telegram_id", "username", "first_name", "last_name")


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "timezone", "morning_enabled", "evening_enabled")
    list_filter = ("timezone", "morning_enabled", "evening_enabled")


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "completed_morning", "completed_evening", "mood")
    list_filter = ("date", "completed_morning", "completed_evening")
    search_fields = ("user__username", "user__telegram_id")


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "period", "order", "is_active")
    list_filter = ("period", "is_active")
    search_fields = ("code", "text")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("daily_entry", "question", "created_at")
    list_filter = ("created_at", "question__period")
    search_fields = ("answer_text", "question_text", "daily_entry__user__username")


@admin.register(WeeklyTask)
class WeeklyTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)


@admin.register(WeeklyCycle)
class WeeklyCycleAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "week_start", "week_end", "is_completed")
    list_filter = ("is_completed", "week_start")
    search_fields = ("user__username",)


@admin.register(NudgePhrase)
class NudgePhraseAdmin(admin.ModelAdmin):
    list_display = ("text", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("text",)


@admin.register(StreakState)
class StreakStateAdmin(admin.ModelAdmin):
    list_display = ("user", "current_streak", "best_streak", "last_completed_date")
    list_filter = ("last_completed_date",)
    search_fields = ("user__username",)
