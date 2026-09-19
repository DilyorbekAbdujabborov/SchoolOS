from rest_framework import serializers

from apps.learning.models import Option, Question
from apps.users.models import StudentProfile

from . import services
from .models import Duel, DuelQuestion, DuelRating


def tier_for_rating(rating: int) -> str:
    if rating >= 1500:
        return "Afsona"
    if rating >= 1300:
        return "Bilimdon"
    if rating >= 1100:
        return "Tajribali"
    return "Yangi boshlovchi"


class DuelOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ("id", "text")


class DuelQuestionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="question_id")
    text = serializers.CharField(source="question.text")
    options = serializers.SerializerMethodField()

    class Meta:
        model = DuelQuestion
        fields = ("id", "order", "text", "options")

    def get_options(self, obj) -> list:
        return DuelOptionSerializer(obj.question.options.all(), many=True).data


class DuelAnswerInputSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    selected_option = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all())

    def validate(self, attrs):
        if attrs["selected_option"].question_id != attrs["question"].id:
            raise serializers.ValidationError("selected_option does not belong to question.")
        return attrs


class DuelSubmitSerializer(serializers.Serializer):
    answers = DuelAnswerInputSerializer(many=True, allow_empty=False)


class DuelCreateSerializer(serializers.Serializer):
    opponent = serializers.PrimaryKeyRelatedField(queryset=StudentProfile.objects.all())

    def create(self, validated_data):
        challenger = self.context["request"].user.student_profile
        try:
            return services.start_duel(challenger=challenger, opponent=validated_data["opponent"])
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class DuelListSerializer(serializers.ModelSerializer):
    """Reframed from "challenger vs opponent" to "me vs my opponent" — the
    client never has to know or care which raw side it's looking at.
    """

    challenger_name = serializers.SerializerMethodField()
    opponent_name = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()
    my_score_percent = serializers.SerializerMethodField()
    opponent_score_percent = serializers.SerializerMethodField()
    i_won = serializers.SerializerMethodField()
    i_have_submitted = serializers.SerializerMethodField()
    opponent_has_submitted = serializers.SerializerMethodField()

    class Meta:
        model = Duel
        fields = (
            "id",
            "challenger",
            "challenger_name",
            "opponent",
            "opponent_name",
            "status",
            "result",
            "my_role",
            "my_score_percent",
            "opponent_score_percent",
            "i_won",
            "i_have_submitted",
            "opponent_has_submitted",
            "created_at",
            "completed_at",
        )

    def get_challenger_name(self, obj) -> str:
        return str(obj.challenger)

    def get_opponent_name(self, obj) -> str:
        return str(obj.opponent)

    def _my_profile(self):
        request = self.context.get("request")
        if request is None:
            return None
        return getattr(request.user, "student_profile", None)

    def get_my_role(self, obj) -> str | None:
        profile = self._my_profile()
        return obj.role_of(profile) if profile else None

    def get_my_score_percent(self, obj) -> float | None:
        role = self.get_my_role(obj)
        return obj.challenger_score_percent if role == "challenger" else obj.opponent_score_percent

    def get_opponent_score_percent(self, obj) -> float | None:
        role = self.get_my_role(obj)
        return obj.opponent_score_percent if role == "challenger" else obj.challenger_score_percent

    def get_i_won(self, obj) -> bool | None:
        if obj.result is None:
            return None
        if obj.result == Duel.Result.DRAW:
            return False
        role = self.get_my_role(obj)
        return (role == "challenger" and obj.result == Duel.Result.CHALLENGER) or (
            role == "opponent" and obj.result == Duel.Result.OPPONENT
        )

    def get_i_have_submitted(self, obj) -> bool:
        role = self.get_my_role(obj)
        submitted_at = obj.challenger_submitted_at if role == "challenger" else obj.opponent_submitted_at
        return submitted_at is not None

    def get_opponent_has_submitted(self, obj) -> bool:
        role = self.get_my_role(obj)
        submitted_at = obj.opponent_submitted_at if role == "challenger" else obj.challenger_submitted_at
        return submitted_at is not None


class DuelRatingSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    school_class_name = serializers.SerializerMethodField()
    tier = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    win_rate = serializers.SerializerMethodField()

    class Meta:
        model = DuelRating
        fields = (
            "rating",
            "tier",
            "wins",
            "losses",
            "draws",
            "total",
            "win_rate",
            "student_name",
            "school_class_name",
        )

    def get_student_name(self, obj) -> str:
        return str(obj.student)

    def get_school_class_name(self, obj) -> str | None:
        return obj.student.school_class.name if obj.student.school_class_id else None

    def get_tier(self, obj) -> str:
        return tier_for_rating(obj.rating)

    def get_total(self, obj) -> int:
        return obj.wins + obj.losses + obj.draws

    def get_win_rate(self, obj) -> int:
        total = obj.wins + obj.losses + obj.draws
        return round(obj.wins / total * 100) if total else 0
