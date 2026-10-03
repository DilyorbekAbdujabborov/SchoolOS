from rest_framework import serializers

from .models import Lesson, Subject, TimetableSlot


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "name")


class LessonSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    school_class_name = serializers.CharField(source="school_class.name", read_only=True)
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            "id",
            "subject",
            "subject_name",
            "school_class",
            "school_class_name",
            "teacher",
            "teacher_name",
            "date",
            "start_time",
            "end_time",
            "room",
            "topic",
        )

    def get_teacher_name(self, obj) -> str:
        return str(obj.teacher)

    def validate(self, attrs):
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        return attrs


class TimetableSlotSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    school_class_name = serializers.CharField(source="school_class.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher_label", read_only=True)
    secondary_teacher_name = serializers.CharField(source="secondary_teacher", read_only=True)
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)

    class Meta:
        model = TimetableSlot
        fields = (
            "id",
            "school_class",
            "school_class_name",
            "subject",
            "subject_name",
            "teacher",
            "teacher_name",
            "secondary_teacher",
            "secondary_teacher_name",
            "day_of_week",
            "day_of_week_display",
            "period_number",
            "start_time",
            "end_time",
            "room",
        )

    def to_internal_value(self, data):
        """Derive missing period times, choosing the class's own shift.

        The director timetable form posts only day/period/subject/teacher/room.
        Times are filled here — not in validate() — because start_time takes part
        in the unique_teacher_slot constraint, so DRF's constraint validator
        demands it while to_internal_value is still running.

        The school runs two shifts with different period lengths (the 13:00 block
        has a 35-minute period 4), so the shift is read off the class's existing
        slots rather than assumed. A class with no slots yet defaults to the first
        shift, and the director can correct the time in the form.
        """
        values = super().to_internal_value(data)
        if values.get("start_time") and values.get("end_time"):
            return values

        period = values.get("period_number")
        if period is None and self.instance is not None:
            period = self.instance.period_number
        if period is None:
            return values

        from apps.school_config.models import SchoolTimeSettings

        # `super().to_internal_value` has already resolved the FK, so this is a
        # SchoolClass instance (on create) or None; fall back to the instance
        # being patched. The bell times belong to the class's tenant, so with no
        # class we can't know whose schedule to read — leave the times untouched.
        school_class = values.get("school_class")
        if school_class is None and self.instance is not None:
            school_class = self.instance.school_class
        if school_class is None:
            return values

        settings_obj = SchoolTimeSettings.get_solo(school_class.organization_id)
        shift = 1
        if settings_obj.second_start_time is not None:
            shift = 2 if TimetableSlot.objects.filter(
                school_class=school_class,
                start_time__gte=settings_obj.second_start_time,
            ).exists() else 1

        start, end = settings_obj.period_times(period, shift=shift)
        values.setdefault("start_time", start)
        values.setdefault("end_time", end)
        return values

    def validate(self, attrs):
        if attrs.get("start_time") and attrs.get("end_time") and attrs["end_time"] <= attrs["start_time"]:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        return attrs

    def get_teacher_name(self, obj) -> str:
        return str(obj.teacher)


class GenerateLessonsSerializer(serializers.Serializer):
    week_start = serializers.DateField()
