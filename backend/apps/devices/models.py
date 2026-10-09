"""Access-control devices: a per-school bridge agent and the physical terminals
it drives.

The cloud side is deliberately vendor-agnostic — no ISAPI, no FDLib, no vendor
event shapes live here. A `Device` only records *what* a terminal is and which
`Bridge` reaches it; all vendor protocol lives in the bridge service's drivers.
"""

import secrets
from typing import ClassVar

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class Bridge(TimeStampedModel):
    """A per-school agent on the LAN that relays terminal events to the cloud and
    pulls commands from it. Authenticates with a bearer token whose hash is all
    the cloud stores."""

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="device_bridges",
        on_delete=models.CASCADE,
    )
    name = models.CharField(_("name"), max_length=120)
    token_hash = models.CharField(_("token hash"), max_length=255, blank=True)
    last_seen_at = models.DateTimeField(_("last seen at"), null=True, blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("device bridge")
        verbose_name_plural = _("device bridges")

    def issue_token(self) -> str:
        """Generate a fresh bearer token, store only its hash, and return the
        plaintext once. The caller must hand it to the bridge now — it is never
        retrievable again."""
        token = secrets.token_urlsafe(32)
        self.token_hash = make_password(token)
        self.save(update_fields=["token_hash", "updated_at"])
        return token

    def check_token(self, token: str) -> bool:
        return bool(self.token_hash) and check_password(token, self.token_hash)

    def __str__(self) -> str:
        return f"{self.name} ({self.organization})"


class Device(TimeStampedModel):
    """A physical terminal (first: Hikvision face terminal) reached over the LAN
    by its `Bridge`."""

    class Direction(models.TextChoices):
        IN = "IN", _("Entry")
        OUT = "OUT", _("Exit")
        BOTH = "BOTH", _("Both")

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="devices",
        on_delete=models.CASCADE,
    )
    bridge = models.ForeignKey(
        Bridge,
        verbose_name=_("bridge"),
        related_name="devices",
        on_delete=models.CASCADE,
    )
    vendor = models.CharField(_("vendor"), max_length=50, blank=True)
    model = models.CharField(_("model"), max_length=100, blank=True)
    serial = models.CharField(_("serial"), max_length=120)
    last_known_ip = models.GenericIPAddressField(_("last known IP"), null=True, blank=True)
    location_label = models.CharField(_("location"), max_length=120, blank=True)
    direction = models.CharField(
        _("direction"),
        max_length=4,
        choices=Direction.choices,
        default=Direction.BOTH,
    )
    capabilities = models.JSONField(_("capabilities"), default=dict, blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("device")
        verbose_name_plural = _("devices")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["organization", "serial"], name="unique_device_serial_per_org"
            ),
        ]

    def save(self, *args, **kwargs):
        if self.organization_id is None and self.bridge_id is not None:
            self.organization_id = self.bridge.organization_id
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.serial} — {self.location_label or self.vendor}"
