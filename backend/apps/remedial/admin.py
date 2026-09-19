from django.contrib import admin

from .models import RemedialSession


@admin.register(RemedialSession)
class RemedialSessionAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "status", "score_percent", "xp_awarded", "created_at")
    list_filter = ("status", "subject")
    search_fields = ("student__user__email",)
    readonly_fields = ("explanation", "questions")
