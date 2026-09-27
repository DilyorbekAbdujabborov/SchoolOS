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
    """Writing a question here is all it takes to make it available to every
    game: the row belongs to a subject, and every game draws from the same
    bank. The class is optional — leave it empty for a question that suits
    every class, or set it to prefer that class when picking (a draw still
    falls back to the rest of the subject, so no student is locked out)."""

    list_display = ("text", "subject", "school_class", "is_active", "created_at")
    list_filter = ("subject", "school_class", "is_active")
    search_fields = ("text", "explanation")
    list_select_related = ("subject", "school_class")
    fields = ("subject", "school_class", "text", "options", "correct_index", "explanation", "is_active")


@admin.register(PooledQuestionServed)
class PooledQuestionServedAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "served_at")
    list_filter = ("served_at",)
    search_fields = ("student__user__email",)
