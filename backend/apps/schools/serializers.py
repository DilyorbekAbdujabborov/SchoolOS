from rest_framework import serializers

from apps.users.models import StudentProfile

from .models import SchoolClass


class SchoolClassSerializer(serializers.ModelSerializer):
    class_teacher_name = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()
    is_my_homeroom = serializers.SerializerMethodField()

    class Meta:
        model = SchoolClass
        fields = (
            "id",
            "name",
            "class_teacher",
            "class_teacher_name",
            "students_count",
            "total_xp",
            "is_my_homeroom",
        )
        read_only_fields = ("total_xp",)

    def get_class_teacher_name(self, obj) -> str | None:
        return str(obj.class_teacher) if obj.class_teacher else None

    def get_students_count(self, obj) -> int:
        return obj.students.count()

    def get_is_my_homeroom(self, obj) -> bool:
        """True when the requesting teacher leads this class — lets the frontend
        pull a teacher's own homeroom class out from the ones they just teach in.
        """
        request = self.context.get("request")
        if request is None:
            return False
        profile = getattr(request.user, "teacher_profile", None)
        return bool(profile and obj.class_teacher_id == profile.pk)


class StudentRosterSerializer(serializers.ModelSerializer):
    """`id` is the StudentProfile pk — the same id Attendance.student and
    bulk-mark expect, not the underlying User's id."""

    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = StudentProfile
        fields = ("id", "full_name", "email")

    def get_full_name(self, obj) -> str:
        return obj.user.get_full_name() or obj.user.username
