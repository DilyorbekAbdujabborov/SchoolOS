from typing import ClassVar

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class XPTransaction(TimeStampedModel):
    """An immutable ledger entry. `StudentProfile.total_xp` is a running sum of
    these — never edit it directly anywhere except `services.award_xp`, which
    is what keeps every XP change auditable back to its source.
    """

    class Source(models.TextChoices):
        TEST = "TEST", _("Test")
        ACTIVITY = "ACTIVITY", _("Activity")
        DUEL = "DUEL", _("Duel")
        REMEDIAL_GAME = "REMEDIAL_GAME", _("Remedial game")
        GAME = "GAME", _("Practice game")
        ACHIEVEMENT = "ACHIEVEMENT", _("Achievement unlocked")

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="xp_transactions",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        "users.StudentProfile",
        verbose_name=_("student"),
        related_name="xp_transactions",
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(_("amount"))
    source = models.CharField(_("source"), max_length=20, choices=Source.choices)
    reason = models.CharField(_("reason"), max_length=255)

    # Points at whichever thing granted the XP (a Test today, an Activity later)
    # without XPTransaction needing a new nullable FK for every new XP source.
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("XP transaction")
        verbose_name_plural = _("XP transactions")
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if self.organization_id is None and self.student_id is not None:
            from apps.common.org import org_id_from_student

            self.organization_id = org_id_from_student(self.student)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student} +{self.amount} XP ({self.source})"


class Achievement(TimeStampedModel):
    """A definition, e.g. 'Perfect Score'. Unlocking is data-driven via
    `condition_type` + `condition_value`, checked by
    `services.CONDITION_CHECKS` — adding a new achievement that reuses an
    existing condition shape is just a new row, no code change.
    """

    class ConditionType(models.TextChoices):
        FIRST_TEST = "FIRST_TEST", _("Complete your first test")
        TEST_COUNT = "TEST_COUNT", _("Complete N tests")
        PERFECT_SCORE = "PERFECT_SCORE", _("Score 100% on a test")
        XP_THRESHOLD = "XP_THRESHOLD", _("Reach a total XP threshold")
        STREAK_LENGTH = "STREAK_LENGTH", _("Reach a streak length")

    name = models.CharField(_("name"), max_length=100, unique=True)
    description = models.CharField(_("description"), max_length=255)
    icon = models.CharField(_("icon"), max_length=10, blank=True)
    condition_type = models.CharField(
        _("condition type"), max_length=20, choices=ConditionType.choices
    )
    condition_value = models.PositiveIntegerField(
        _("condition value"),
        default=0,
        help_text=_("Meaning depends on condition_type, e.g. an XP or streak-day threshold."),
    )
    xp_reward = models.PositiveIntegerField(
        _("XP reward"),
        default=0,
        help_text=_("Awarded once, the moment a student unlocks this achievement."),
    )
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("achievement")
        verbose_name_plural = _("achievements")
        ordering = ("condition_type", "condition_value")

    def __str__(self) -> str:
        return self.name


class StudentAchievement(TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="student_achievements",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        "users.StudentProfile",
        verbose_name=_("student"),
        related_name="unlocked_achievements",
        on_delete=models.CASCADE,
    )
    achievement = models.ForeignKey(
        Achievement,
        verbose_name=_("achievement"),
        related_name="unlocks",
        on_delete=models.CASCADE,
    )
    unlocked_at = models.DateTimeField(_("unlocked at"), auto_now_add=True)

    class Meta:
        verbose_name = _("student achievement")
        verbose_name_plural = _("student achievements")
        ordering = ("-unlocked_at",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["organization", "student", "achievement"],
                name="unique_student_achievement_per_org",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.organization_id is None and self.student_id is not None:
            from apps.common.org import org_id_from_student

            self.organization_id = org_id_from_student(self.student)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student} unlocked {self.achievement} at {self.organization}"


class Streak(TimeStampedModel):
    """Consecutive days of activity *in one organization*.

    Was a OneToOne on student — one streak for the whole account. With several
    organizations on one account that would make a club's activity days extend
    the school's streak, so this is now unique per (organization, student).
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="streaks",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        "users.StudentProfile",
        verbose_name=_("student"),
        related_name="streaks",
        on_delete=models.CASCADE,
    )
    current_streak = models.PositiveIntegerField(_("current streak"), default=0)
    longest_streak = models.PositiveIntegerField(_("longest streak"), default=0)
    last_activity_date = models.DateField(_("last activity date"), null=True, blank=True)

    class Meta:
        verbose_name = _("streak")
        verbose_name_plural = _("streaks")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["organization", "student"], name="unique_streak_per_student_org"
            ),
        ]

    def save(self, *args, **kwargs):
        if self.organization_id is None and self.student_id is not None:
            from apps.common.org import org_id_from_student

            self.organization_id = org_id_from_student(self.student)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student} @ {self.organization}: {self.current_streak} day streak"


class LeagueStanding(TimeStampedModel):
    """Which weekly league tier a student currently sits in, per organization.

    Tiers are plain integers (1 = Bronza … 9 = Afsona — see
    `apps.gamification.league.LEAGUE_TIERS`). Ranking *inside* a tier is by XP
    earned this week and is computed live from `XPTransaction`, so it is never
    stored here; only the tier itself persists, because that is what carries over
    between weeks as students are promoted and relegated.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="league_standings",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        "users.StudentProfile",
        verbose_name=_("student"),
        related_name="league_standings",
        on_delete=models.CASCADE,
    )
    tier = models.PositiveSmallIntegerField(_("tier"), default=1)

    class Meta:
        verbose_name = _("league standing")
        verbose_name_plural = _("league standings")
        ordering = ("-tier",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["organization", "student"], name="unique_league_standing_per_org"
            ),
        ]

    def save(self, *args, **kwargs):
        if self.organization_id is None and self.student_id is not None:
            from apps.common.org import org_id_from_student

            self.organization_id = org_id_from_student(self.student)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student} @ tier {self.tier}"


class WeeklyGoal(TimeStampedModel):
    """A student's personal weekly XP target and how many weeks running they have
    hit it. Progress toward the current week is computed live from `XPTransaction`;
    only the target and the streak counters persist here. `last_completed_week`
    (a Monday date) makes the weekly roll-up idempotent — a week is counted once.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="weekly_goals",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        "users.StudentProfile",
        verbose_name=_("student"),
        related_name="weekly_goals",
        on_delete=models.CASCADE,
    )
    target_xp = models.PositiveIntegerField(_("weekly XP target"), default=500)
    goal_streak = models.PositiveIntegerField(_("weeks hit in a row"), default=0)
    best_goal_streak = models.PositiveIntegerField(_("best weekly streak"), default=0)
    last_completed_week = models.DateField(_("last completed week"), null=True, blank=True)

    class Meta:
        verbose_name = _("weekly goal")
        verbose_name_plural = _("weekly goals")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["organization", "student"], name="unique_weekly_goal_per_org"
            ),
        ]

    def save(self, *args, **kwargs):
        if self.organization_id is None and self.student_id is not None:
            from apps.common.org import org_id_from_student

            self.organization_id = org_id_from_student(self.student)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student}: {self.target_xp} XP/week"


class LeagueCycle(TimeStampedModel):
    """A marker that one organization's weekly league roll-up has already run for
    a given (just-ended) week. Promotion/relegation is not idempotent on its own —
    running it twice would move everyone twice — so the weekly task records the
    week here and skips a week it has already processed."""

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="league_cycles",
        on_delete=models.CASCADE,
    )
    week_start = models.DateField(_("processed week (Monday)"))

    class Meta:
        verbose_name = _("league cycle")
        verbose_name_plural = _("league cycles")
        ordering = ("-week_start",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["organization", "week_start"], name="unique_league_cycle_per_org_week"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.organization} · week of {self.week_start}"
