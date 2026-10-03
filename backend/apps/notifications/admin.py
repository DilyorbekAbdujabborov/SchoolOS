from django.contrib import admin

from .models import Notification, PushSubscription


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "category", "is_read", "created_at")
    list_filter = ("category", "is_read")
    search_fields = ("title", "body", "recipient__email")


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "endpoint", "created_at")
    search_fields = ("user__email", "endpoint")
