from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    class Category(models.TextChoices):
        GENERAL = "GENERAL", _("General")
        ATTENDANCE = "ATTENDANCE", _("Attendance")
        TEST_PUBLISHED = "TEST_PUBLISHED", _("Test published")
        TEST_RESULT = "TEST_RESULT", _("Test result")
        ACTIVITY_PUBLISHED = "ACTIVITY_PUBLISHED", _("Activity published")
        ACTIVITY_RESULT = "ACTIVITY_RESULT", _("Activity graded")
        XP_EARNED = "XP_EARNED", _("XP earned")
        ACHIEVEMENT_UNLOCKED = "ACHIEVEMENT_UNLOCKED", _("Achievement unlocked")
        STREAK = "STREAK", _("Streak")
        LESSON_REMINDER = "LESSON_REMINDER", _("Lesson reminder")
        TASK_ASSIGNED = "TASK_ASSIGNED", _("Task assigned")
        DUEL_INVITE = "DUEL_INVITE", _("Duel invite")
        DUEL_RESULT = "DUEL_RESULT", _("Duel result")

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("recipient"),
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="notifications",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_(
            "Which organization raised this notification. Required for anything "
            "generated inside one; NULL is reserved for platform-level messages."
        ),
    )
    title = models.CharField(_("title"), max_length=255)
    body = models.TextField(_("body"))
    category = models.CharField(
        _("category"), max_length=20, choices=Category.choices, default=Category.GENERAL
    )
    is_read = models.BooleanField(_("is read"), default=False)

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} -> {self.recipient}"


class PushSubscription(TimeStampedModel):
    """A browser Web Push endpoint a user opted into, one row per device/browser.

    `notify()` fans a message out to every live subscription its recipient has;
    a subscription that the push service reports as gone (404/410) is deleted on
    the next send, so dead endpoints don't pile up.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        related_name="push_subscriptions",
        on_delete=models.CASCADE,
    )
    endpoint = models.URLField(_("endpoint"), max_length=500, unique=True)
    p256dh = models.CharField(_("p256dh key"), max_length=200)
    auth = models.CharField(_("auth secret"), max_length=100)

    class Meta:
        verbose_name = _("push subscription")
        verbose_name_plural = _("push subscriptions")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Push subscription for {self.user}"
