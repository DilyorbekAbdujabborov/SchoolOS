from django.contrib import admin

from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "school_name", "status", "created_at")
    list_filter = ("status", "created_at")
    list_editable = ("status",)
    search_fields = ("name", "phone", "school_name", "message")
    readonly_fields = ("name", "phone", "school_name", "message", "created_at", "updated_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        # Leads only ever arrive through the public form, never typed in by hand.
        return False
