from django.contrib import admin

from .models import ParentLinkCode, ParentTelegramAccount, TelegramAccount, TelegramLinkCode


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_id", "telegram_username", "created_at")
    search_fields = ("user__email", "telegram_username")


@admin.register(TelegramLinkCode)
class TelegramLinkCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "expires_at", "used_at")
    search_fields = ("code", "user__email")


@admin.register(ParentTelegramAccount)
class ParentTelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("student", "telegram_id", "telegram_username", "created_at")
    search_fields = ("student__user__email", "telegram_username")


@admin.register(ParentLinkCode)
class ParentLinkCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "student", "expires_at", "used_at")
    search_fields = ("code", "student__user__email")
