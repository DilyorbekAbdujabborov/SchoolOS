from django.contrib import admin

from .models import GameSession


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "game_type", "status", "score_percent", "xp_awarded", "created_at")
    list_filter = ("game_type", "status", "subject")
    search_fields = ("student__user__email",)
    readonly_fields = ("questions",)
