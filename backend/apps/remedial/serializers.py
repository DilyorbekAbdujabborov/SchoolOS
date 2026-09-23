from rest_framework import serializers

from .models import RemedialSession


class RemedialSessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    # "TEST" or "GAME" — what the low score came from — and a title for it.
    source = serializers.SerializerMethodField()
    test_title = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = RemedialSession
        fields = (
            "id",
            "attempt",
            "game_session",
            "source",
            "subject",
            "subject_name",
            "test_title",
            "status",
            "explanation",
            "question_count",
            "score_percent",
            "xp_awarded",
            "created_at",
            "completed_at",
        )
        read_only_fields = fields

    def get_question_count(self, obj) -> int:
        return len(obj.questions)

    def get_source(self, obj) -> str:
        return "TEST" if obj.attempt_id else "GAME"

    def get_test_title(self, obj) -> str:
        if obj.attempt_id:
            return obj.attempt.test.title
        return obj.game_session.get_game_type_display()


class RemedialGameQuestionSerializer(serializers.Serializer):
    """Answer-free — same principle as `learning.QuestionSerializer` for a `Test`."""

    text = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())


class RemedialAnswerInputSerializer(serializers.Serializer):
    question_index = serializers.IntegerField(min_value=0)
    selected_index = serializers.IntegerField(min_value=0)


class RemedialSubmitSerializer(serializers.Serializer):
    answers = RemedialAnswerInputSerializer(many=True, allow_empty=False)
