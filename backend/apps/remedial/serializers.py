from rest_framework import serializers

from .models import RemedialSession


class RemedialSessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    test_title = serializers.CharField(source="attempt.test.title", read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = RemedialSession
        fields = (
            "id",
            "attempt",
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


class RemedialGameQuestionSerializer(serializers.Serializer):
    """Answer-free — same principle as `learning.QuestionSerializer` for a `Test`."""

    text = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())


class RemedialAnswerInputSerializer(serializers.Serializer):
    question_index = serializers.IntegerField(min_value=0)
    selected_index = serializers.IntegerField(min_value=0)


class RemedialSubmitSerializer(serializers.Serializer):
    answers = RemedialAnswerInputSerializer(many=True, allow_empty=False)
