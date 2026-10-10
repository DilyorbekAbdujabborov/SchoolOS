from django.contrib import admin

from .models import Bridge, Device


@admin.register(Bridge)
class BridgeAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "is_active", "last_seen_at")
    list_filter = ("is_active",)
    search_fields = ("name", "organization__name")
    readonly_fields = ("token_hash", "last_seen_at")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("serial", "organization", "bridge", "direction", "is_active", "last_known_ip")
    list_filter = ("direction", "is_active", "vendor")
    search_fields = ("serial", "location_label", "organization__name")
    autocomplete_fields = ("bridge",)
