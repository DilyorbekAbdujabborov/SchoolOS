from rest_framework import serializers

from apps.academics.models import Subject
from apps.schools.models import SchoolClass

from . import services
from .models import GameSession


class GameSessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    game_type_display = serializers.CharField(source="get_game_type_display", read_only=True)
    question_count = serializers.SerializerMethodField()
    # Server-recorded progress, so a game that locks answers in as it goes
    # (Minora qurish) can resume after a page reload. Always 0 for the others.
    answered_count = serializers.SerializerMethodField()
    correct_count = serializers.SerializerMethodField()
    max_xp = serializers.SerializerMethodField()
    # Kodni buzish: the code as far as it's been earned (null = locked segment).
    # Kodni buzish / Xazina ovi: the win threshold and whether it was reached.
    # Live-key games, once over: the per-question review.
    revealed_code = serializers.SerializerMethodField()
    # Jang maydoni: server-computed HP / combo / round state (null for other games).
    battle = serializers.SerializerMethodField()
    goal_reached = serializers.SerializerMethodField()
    unlock_percent = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()
    # Set once a low score has opened an AI-tutor session for this game (apps.remedial).
    remedial_session_id = serializers.SerializerMethodField()

    class Meta:
        model = GameSession
        fields = (
            "id",
            "subject",
            "subject_name",
            "game_type",
            "game_type_display",
            "status",
            "question_count",
            "answered_count",
            "correct_count",
            "max_xp",
            "revealed_code",
            "battle",
            "goal_reached",
            "unlock_percent",
            "review",
            "remedial_session_id",
            "score_percent",
            "xp_awarded",
            "created_at",
            "completed_at",
        )
        read_only_fields = fields

    def get_question_count(self, obj) -> int:
        return len(obj.questions) or services.question_count_for(obj.game_type)

    def get_answered_count(self, obj) -> int:
        return len(obj.answers or {})

    def get_correct_count(self, obj) -> int:
        return services.correct_answer_count(obj, services.recorded_answers(obj))

    def get_max_xp(self, obj) -> int:
        return services.max_xp_for(obj.game_type)

    def get_revealed_code(self, obj) -> list[str | None]:
        return services.revealed_code(obj)

    def get_battle(self, obj) -> dict | None:
        return services.battle_state(obj)

    def get_goal_reached(self, obj) -> bool:
        return services.is_goal_reached(obj)

    def get_unlock_percent(self, obj) -> int | None:
        return services.unlock_percent_for(obj.game_type)

    def get_remedial_session_id(self, obj) -> int | None:
        remedial = next(iter(obj.remedial_sessions.all()), None)
        return remedial.id if remedial else None

    def get_review(self, obj) -> list[dict] | None:
        # The history list doesn't need every past game's full question set.
        view = self.context.get("view")
        if view is not None and getattr(view, "action", None) == "list":
            return None
        return services.answer_review(obj)


class GameQuestionSerializer(serializers.Serializer):
    """Answer-free — same principle as `learning.QuestionSerializer` for a `Test`."""

    text = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())


class GameSessionCreateSerializer(serializers.Serializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    game_type = serializers.ChoiceField(choices=GameSession.GameType.choices)

    def create(self, validated_data):
        student = self.context["request"].user.student_profile
        return services.start_game(
            student=student, subject=validated_data["subject"], game_type=validated_data["game_type"]
        )


class GameAnswerInputSerializer(serializers.Serializer):
    question_index = serializers.IntegerField(min_value=0)
    # -1 means "timed out on this question" (see GameAnswerCheckSerializer) —
    # the frontend always includes a timed-out question in the final submit
    # payload, so rejecting -1 here made every game where the student ever
    # let the clock run out on a single question fail to submit entirely.
    selected_index = serializers.IntegerField(min_value=-1)


class GameSubmitSerializer(serializers.Serializer):
    answers = GameAnswerInputSerializer(many=True, allow_empty=False)


class GameAnswerCheckSerializer(serializers.Serializer):
    """A single live answer check — `selected_index` may be -1 for a timeout (never correct)."""

    question_index = serializers.IntegerField(min_value=0)
    selected_index = serializers.IntegerField(min_value=-1)


class PoolRefillSerializer(serializers.Serializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    school_class = serializers.PrimaryKeyRelatedField(queryset=SchoolClass.objects.all())
