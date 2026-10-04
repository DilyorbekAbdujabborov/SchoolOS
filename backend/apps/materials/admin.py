from django.contrib import admin

from .models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "kind", "organization", "uploaded_by", "created_at")
    list_filter = ("kind", "subject", "organization")
    search_fields = ("title", "description")
    raw_id_fields = ("subject", "uploaded_by", "organization")
