from rest_framework import serializers

from apps.academics.models import Subject
from apps.schools.models import SchoolClass

from . import services
from .models import GameSession


class GameSessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    game_type_display = serializers.CharField(source="get_game_type_display", read_only=True)
    question_count = serializers.SerializerMethodField()

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
            "score_percent",
            "xp_awarded",
            "created_at",
            "completed_at",
        )
        read_only_fields = fields

    def get_question_count(self, obj) -> int:
        return len(obj.questions)


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
