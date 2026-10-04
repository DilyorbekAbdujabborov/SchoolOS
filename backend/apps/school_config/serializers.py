from rest_framework import serializers

from .models import SchoolTimeSettings


class ClassAccessClassSerializer(serializers.Serializer):
    """One class's open/closed state inside the teacher's access status."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    expires_at = serializers.DateTimeField(allow_null=True)


class ClassAccessStatusSerializer(serializers.Serializer):
    """Whether the teacher's classes are currently open, and until when."""

    open = serializers.BooleanField()
    expires_at = serializers.DateTimeField(allow_null=True)
    classes = ClassAccessClassSerializer(many=True)


class SchoolTimeSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolTimeSettings
        fields = (
            "start_time",
            "end_time",
            "period_duration_minutes",
            "short_break_minutes",
            "long_break_after_period",
            "long_break_minutes",
            "second_start_time",
            "second_short_period",
            "second_short_period_minutes",
        )
