from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel

#: ISO weekdays (1=Mon … 7=Sun) the School Time Lock is active on by default —
#: Monday through Saturday, so Sunday is open. A module-level callable so the
#: migration can serialize it.
DEFAULT_SCHOOL_DAYS = [1, 2, 3, 4, 5, 6]


def default_school_days() -> list[int]:
    return list(DEFAULT_SCHOOL_DAYS)


class SchoolTimeSettings(TimeStampedModel):
    """School-day timing for exactly one organization.

    `start_time`/`end_time` gate the School Time Lock (see middleware.py).
    The period-timing fields let the timetable auto-compute each period's
    start/end time from just a period number, instead of the director typing
    times for every single slot.

    This was a `pk = 1` singleton. It is now one row per organization, enforced
    by a real `OneToOneField` — the old `save()` override silently rewrote every
    row to pk 1, which would have collapsed all organizations onto one another's
    timings. `get_solo()` still creates the row on demand, so callers that
    already treat the settings as always-present keep working.
    """

    organization = models.OneToOneField(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="time_settings",
        on_delete=models.CASCADE,
    )
    start_time = models.TimeField(_("school start time"), default=time(8, 0))
    end_time = models.TimeField(_("school end time"), default=time(13, 10))
    school_days = models.JSONField(
        _("school days"),
        default=default_school_days,
        help_text=_(
            "ISO weekdays the lock is active on (1=Mon … 7=Sun). "
            "Default is Mon–Sat, so Sunday is open."
        ),
    )

    period_duration_minutes = models.PositiveSmallIntegerField(
        _("period duration (minutes)"), default=45
    )
    short_break_minutes = models.PositiveSmallIntegerField(_("short break (minutes)"), default=5)
    long_break_after_period = models.PositiveSmallIntegerField(
        _("long break after period"), default=4
    )
    long_break_minutes = models.PositiveSmallIntegerField(_("long break (minutes)"), default=20)

    # Second daily shift. It is not a copy of the first one: the 13:00 block runs
    # a 35-minute period 4, so its times cannot be derived by shifting the 08:00
    # block and have to be described in their own right.
    second_start_time = models.TimeField(
        _("second shift start time"),
        null=True,
        blank=True,
        help_text=_("Leave empty when the school runs a single shift."),
    )
    second_short_period = models.PositiveSmallIntegerField(
        _("second shift short period"),
        default=4,
        help_text=_("Which period of the second shift is shorter than the standard duration."),
    )
    second_short_period_minutes = models.PositiveSmallIntegerField(
        _("second shift short period (minutes)"),
        default=35,
    )

    class Meta:
        verbose_name = _("school time settings")
        verbose_name_plural = _("school time settings")

    def __str__(self) -> str:
        return f"{self.organization}: {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    @classmethod
    def get_solo(cls, organization) -> "SchoolTimeSettings":
        """The settings for `organization`, created with defaults if absent.

        `organization` is required — there is no "the" settings row any more,
        and defaulting to one would hand a club the school's bell times.
        """
        if organization is None:
            raise ValueError("SchoolTimeSettings.get_solo() requires an organization.")
        # Accept either an Organization instance or its pk, so callers that only
        # have an id (a serializer with a class's organization_id, say) don't
        # have to fetch the row just to pass it here.
        if isinstance(organization, int):
            obj, _created = cls.objects.get_or_create(organization_id=organization)
        else:
            obj, _created = cls.objects.get_or_create(organization=organization)
        return obj

    def is_school_day(self, day) -> bool:
        """Whether `day` (a date) is a day the lock applies on. Days off — Sunday
        by default — are never locked, so weekends stay open."""
        return day.isoweekday() in (self.school_days or DEFAULT_SCHOOL_DAYS)

    def is_locked_at(self, current_time) -> bool:
        if self.start_time <= self.end_time:
            return self.start_time <= current_time < self.end_time
        return current_time >= self.start_time or current_time < self.end_time

    def shift_start(self, shift: int) -> time:
        """Start time of `shift` (1 or 2); falls back to the first shift."""
        if shift == 2 and self.second_start_time is not None:
            return self.second_start_time
        return self.start_time

    def period_duration(self, period_number: int, shift: int) -> int:
        """Minutes the given period lasts. The second shift shortens one period."""
        if (
            shift == 2
            and self.second_start_time is not None
            and period_number == self.second_short_period
        ):
            return self.second_short_period_minutes
        return self.period_duration_minutes

    def current_period_end(self, now_time) -> time:
        """End of the lesson period `now_time` sits in, or of the next one if it
        sits in a break. Falls back to the lock window's end. Used as a last
        resort for the class-access window when a teacher has no dated lesson to
        anchor it to (see school_config.services)."""
        period = 1
        while period <= 20:  # a school day is never this long — just a guard
            start, end = self.period_times(period, shift=1)
            if start >= self.end_time:
                break
            if end > now_time:
                return min(end, self.end_time)
            period += 1
        return self.end_time

    def period_times(self, period_number: int, shift: int = 1) -> tuple[time, time]:
        """Start/end time of the Nth period of `shift`, counting breaks since that
        shift's start.

        `shift` is 1 or 2. The second shift is optional: when `second_start_time`
        is empty the helper behaves as if the school ran a single shift.
        """
        # The date is an arbitrary anchor — only the resulting .time() is used.
        current = datetime.combine(date(2000, 1, 1), self.shift_start(shift))
        for period in range(1, period_number):
            current += timedelta(minutes=self.period_duration(period, shift))
            break_minutes = (
                self.long_break_minutes
                if period == self.long_break_after_period
                else self.short_break_minutes
            )
            current += timedelta(minutes=break_minutes)
        period_start = current.time()
        period_end = (current + timedelta(minutes=self.period_duration(period_number, shift))).time()
        return period_start, period_end


class ClassAccessWindow(TimeStampedModel):
    """A temporary lift of the School Time Lock for one class.

    A teacher (including a class's own `class_teacher`) opens the platform for
    their classes during a lesson; each opened class gets a row here that expires
    at the end of the current period. The lock middleware lets a student through
    while their class has a row whose `expires_at` is still in the future, so a
    teacher who forgets to close it never leaves the class open past the bell.
    """

    school_class = models.OneToOneField(
        "schools.SchoolClass",
        verbose_name=_("class"),
        related_name="access_window",
        on_delete=models.CASCADE,
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("opened by"),
        related_name="opened_access_windows",
        null=True,
        on_delete=models.SET_NULL,
    )
    expires_at = models.DateTimeField(_("expires at"))

    class Meta:
        verbose_name = _("class access window")
        verbose_name_plural = _("class access windows")
        ordering = ("-expires_at",)

    def __str__(self) -> str:
        return f"{self.school_class} until {self.expires_at:%H:%M}"

    def is_active(self, now=None) -> bool:
        return self.expires_at > (now or timezone.now())
