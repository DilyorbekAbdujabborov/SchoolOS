from typing import ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class Duel(TimeStampedModel):
    """A 1-v-1 async quiz battle between two classmates — same random
    question set for both, whoever scores higher (then, on a tie, whoever
    answered faster) wins. Fields are duplicated challenger_*/opponent_*
    rather than normalized into a participant table, since a duel only ever
    has exactly two sides.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        COMPLETED = "COMPLETED", _("Completed")

    class Result(models.TextChoices):
        CHALLENGER = "CHALLENGER", _("Challenger won")
        OPPONENT = "OPPONENT", _("Opponent won")
        DRAW = "DRAW", _("Draw")

    challenger = models.ForeignKey(
        "users.StudentProfile", verbose_name=_("challenger"), related_name="duels_as_challenger",
        on_delete=models.CASCADE,
    )
    opponent = models.ForeignKey(
        "users.StudentProfile", verbose_name=_("opponent"), related_name="duels_as_opponent",
        on_delete=models.CASCADE,
    )
    school_class = models.ForeignKey(
        "schools.SchoolClass", verbose_name=_("class"), related_name="duels", on_delete=models.CASCADE
    )
    status = models.CharField(_("status"), max_length=20, choices=Status.choices, default=Status.ACTIVE)
    result = models.CharField(_("result"), max_length=20, choices=Result.choices, null=True, blank=True)

    challenger_started_at = models.DateTimeField(_("challenger started at"), null=True, blank=True)
    challenger_submitted_at = models.DateTimeField(_("challenger submitted at"), null=True, blank=True)
    challenger_score_percent = models.FloatField(_("challenger score (%)"), null=True, blank=True)

    opponent_started_at = models.DateTimeField(_("opponent started at"), null=True, blank=True)
    opponent_submitted_at = models.DateTimeField(_("opponent submitted at"), null=True, blank=True)
    opponent_score_percent = models.FloatField(_("opponent score (%)"), null=True, blank=True)

    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("duel")
        verbose_name_plural = _("duels")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.challenger} vs {self.opponent} ({self.status})"

    def role_of(self, student_profile) -> str | None:
        if student_profile.pk == self.challenger_id:
            return "challenger"
        if student_profile.pk == self.opponent_id:
            return "opponent"
        return None


class DuelQuestion(TimeStampedModel):
    """A snapshot of one randomly-picked question for a duel — picked once at
    creation so a later edit to the question bank never changes an in-flight duel.
    """

    duel = models.ForeignKey(Duel, verbose_name=_("duel"), related_name="duel_questions", on_delete=models.CASCADE)
    question = models.ForeignKey(
        "learning.Question", verbose_name=_("question"), related_name="+", on_delete=models.CASCADE
    )
    order = models.PositiveSmallIntegerField(_("order"), default=0)

    class Meta:
        verbose_name = _("duel question")
        verbose_name_plural = _("duel questions")
        ordering = ("order", "id")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(fields=["duel", "question"], name="unique_duel_question"),
        ]

    def __str__(self) -> str:
        return f"{self.duel} — Q{self.order}"


class DuelAnswer(TimeStampedModel):
    duel = models.ForeignKey(Duel, verbose_name=_("duel"), related_name="answers", on_delete=models.CASCADE)
    participant = models.ForeignKey(
        "users.StudentProfile", verbose_name=_("participant"), related_name="duel_answers",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        "learning.Question", verbose_name=_("question"), related_name="+", on_delete=models.CASCADE
    )
    selected_option = models.ForeignKey(
        "learning.Option", verbose_name=_("selected option"), related_name="+", on_delete=models.CASCADE
    )
    is_correct = models.BooleanField(_("is correct"), default=False)

    class Meta:
        verbose_name = _("duel answer")
        verbose_name_plural = _("duel answers")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["duel", "participant", "question"], name="unique_duel_participant_answer"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.duel} — {self.participant} — {self.question_id}"


class DuelRating(TimeStampedModel):
    """A student's duel ELO-lite rating — separate from `StudentProfile` the
    same way `Streak` is, so the gamification side-stats don't crowd the
    core account model.
    """

    DEFAULT_RATING = 1200

    student = models.OneToOneField(
        "users.StudentProfile", verbose_name=_("student"), related_name="duel_rating", on_delete=models.CASCADE
    )
    rating = models.PositiveIntegerField(_("rating"), default=DEFAULT_RATING)
    wins = models.PositiveIntegerField(_("wins"), default=0)
    losses = models.PositiveIntegerField(_("losses"), default=0)
    draws = models.PositiveIntegerField(_("draws"), default=0)

    class Meta:
        verbose_name = _("duel rating")
        verbose_name_plural = _("duel ratings")
        ordering = ("-rating",)

    def __str__(self) -> str:
        return f"{self.student} — {self.rating}"
