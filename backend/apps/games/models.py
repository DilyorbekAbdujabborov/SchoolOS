from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class GameSession(TimeStampedModel):
    """A self-serve AI practice game — pick a subject, pick a game, play.
    Unlike `apps.remedial.RemedialSession`, this isn't triggered by a low
    test score and isn't tied to any particular `TestAttempt`; a student can
    start one any time from the "O'yinlar" section. Same question-snapshot
    approach (see that app for why).
    """

    class GameType(models.TextChoices):
        TUG_OF_WAR = "TUG_OF_WAR", _("Arqon tortish")
        QUIZ = "QUIZ", _("Viktorina")

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        COMPLETED = "COMPLETED", _("Completed")

    student = models.ForeignKey(
        "users.StudentProfile", verbose_name=_("student"), related_name="game_sessions", on_delete=models.CASCADE
    )
    subject = models.ForeignKey(
        "academics.Subject", verbose_name=_("subject"), related_name="+", on_delete=models.CASCADE
    )
    game_type = models.CharField(_("game type"), max_length=20, choices=GameType.choices)
    status = models.CharField(_("status"), max_length=20, choices=Status.choices, default=Status.ACTIVE)
    # [{"text": str, "options": [str, ...], "correct_index": int}, ...] — AI-generated snapshot.
    questions = models.JSONField(_("questions"), default=list, blank=True)
    score_percent = models.FloatField(_("score (%)"), null=True, blank=True)
    xp_awarded = models.PositiveSmallIntegerField(_("XP awarded"), null=True, blank=True)
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("game session")
        verbose_name_plural = _("game sessions")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.student} — {self.subject} — {self.get_game_type_display()} ({self.status})"
