# gratitude_bot/core/services/streak.py
from datetime import timedelta
from core.models import StreakState


def update_streak_on_activity(user, activity_date):
    streak, _ = StreakState.objects.get_or_create(user=user)

    # уже засчитали этот день
    if streak.last_completed_date == activity_date:
        return streak

    if streak.last_completed_date == activity_date - timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    if streak.current_streak > streak.best_streak:
        streak.best_streak = streak.current_streak

    streak.last_completed_date = activity_date
    streak.save(update_fields=["current_streak", "best_streak", "last_completed_date"])
    return streak
