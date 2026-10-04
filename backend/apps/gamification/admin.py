from django.contrib import admin

from .models import (
    Achievement,
    LeagueCycle,
    LeagueStanding,
    Streak,
    StudentAchievement,
    WeeklyGoal,
    XPTransaction,
)


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ("student", "amount", "source", "created_at")
    list_filter = ("source",)
    search_fields = ("student__user__email", "reason")
    autocomplete_fields = ("student",)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "condition_type", "condition_value", "is_active")
    list_filter = ("condition_type", "is_active")
    search_fields = ("name",)


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ("student", "achievement", "unlocked_at")
    autocomplete_fields = ("student", "achievement")


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ("student", "current_streak", "longest_streak", "last_activity_date")
    autocomplete_fields = ("student",)


@admin.register(LeagueStanding)
class LeagueStandingAdmin(admin.ModelAdmin):
    list_display = ("student", "organization", "tier")
    list_filter = ("tier",)
    raw_id_fields = ("organization", "student")


@admin.register(WeeklyGoal)
class WeeklyGoalAdmin(admin.ModelAdmin):
    list_display = ("student", "target_xp", "goal_streak", "best_goal_streak", "last_completed_week")
    raw_id_fields = ("organization", "student")


@admin.register(LeagueCycle)
class LeagueCycleAdmin(admin.ModelAdmin):
    list_display = ("organization", "week_start")
    raw_id_fields = ("organization",)
