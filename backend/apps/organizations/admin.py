from django import forms
from django.contrib import admin

from .capabilities import ACTIONS, RESOURCES, all_keys
from .models import ClientConfig, Organization, OrganizationMembership


class ClientConfigForm(forms.ModelForm):
    """`denied` as a resource × action checkbox grid instead of raw JSON."""

    denied = forms.MultipleChoiceField(
        choices=[
            (f"{key}.{action}", f"{resource.label} — {action}")
            for key, resource in RESOURCES.items()
            for action in ACTIONS
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Taqiqlangan imkoniyatlar",
        help_text="'read' belgilansa butun bo'lim yopiladi (sidebar va API).",
    )

    class Meta:
        model = ClientConfig
        fields = ("denied",)

    def clean_denied(self):
        return [key for key in all_keys() if key in self.cleaned_data["denied"]]


class ClientConfigInline(admin.StackedInline):
    model = ClientConfig
    form = ClientConfigForm
    can_delete = False
    max_num = 1

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    has_add_permission = has_change_permission = (
        lambda self, request, obj=None: request.user.is_superuser
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "type", "timezone", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ClientConfigInline,)


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role", "status")
    list_filter = ("role", "status", "organization__type")
    search_fields = ("user__email", "user__first_name", "user__last_name", "organization__name")
