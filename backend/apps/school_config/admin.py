from django.contrib import admin

from .models import ClassAccessWindow, SchoolTimeSettings


@admin.register(ClassAccessWindow)
class ClassAccessWindowAdmin(admin.ModelAdmin):
    list_display = ("school_class", "opened_by", "expires_at")
    raw_id_fields = ("school_class", "opened_by")


@admin.register(SchoolTimeSettings)
class SchoolTimeSettingsAdmin(admin.ModelAdmin):
    list_display = ("start_time", "end_time", "second_start_time")

    def has_add_permission(self, request):
        return not SchoolTimeSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
