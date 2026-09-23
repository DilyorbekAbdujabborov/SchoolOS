from django.contrib import admin

from .models import GameSession, PooledQuestion, PooledQuestionServed


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "game_type", "status", "score_percent", "xp_awarded", "created_at")
    list_filter = ("game_type", "status", "subject")
    search_fields = ("student__user__email",)
    readonly_fields = ("questions", "answers")


@admin.register(PooledQuestion)
class PooledQuestionAdmin(admin.ModelAdmin):
    list_display = ("subject", "school_class", "text", "created_at")
    list_filter = ("subject", "school_class")
    search_fields = ("text",)


@admin.register(PooledQuestionServed)
class PooledQuestionServedAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "served_at")
    list_filter = ("served_at",)
    search_fields = ("student__user__email",)
