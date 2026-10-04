"""Demo requests from the public marketing landing page.

A prospective school fills in the "Bepul demo so'rash" form on `/`; the
submission lands here. These are pre-sale leads, not tenants — they belong to
no organization and need no account. The SchoolOS team works them from the
Django admin, moving each through `status` as they call back and follow up.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class DemoRequest(TimeStampedModel):
    """One "request a demo" submission from the landing page."""

    class Status(models.TextChoices):
        NEW = "new", _("Yangi")
        CONTACTED = "contacted", _("Bog'lanildi")
        CLOSED = "closed", _("Yopildi")

    name = models.CharField(_("ism"), max_length=120)
    phone = models.CharField(_("telefon"), max_length=32)
    school_name = models.CharField(_("maktab nomi"), max_length=200, blank=True)
    message = models.TextField(_("xabar"), blank=True)
    status = models.CharField(
        _("holat"),
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
    )

    class Meta:
        verbose_name = _("demo so'rovi")
        verbose_name_plural = _("demo so'rovlari")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"
