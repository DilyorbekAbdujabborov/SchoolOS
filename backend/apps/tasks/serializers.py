from rest_framework import serializers

from apps.users.models import TeacherProfile

from .models import TeacherTask, TeacherTaskAssignment
from .services import assign_task


class TeacherTaskWriteSerializer(serializers.ModelSerializer):
    """Director-only: creates the task and fans it out to its recipient(s) in one call."""

    teacher = serializers.PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(), required=False, allow_null=True, write_only=True
    )
    send_to_all = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = TeacherTask
        fields = ("id", "title", "description", "category", "teacher", "send_to_all", "is_broadcast", "created_at")
        read_only_fields = ("id", "is_broadcast", "created_at")

    def validate(self, attrs):
        teacher = attrs.get("teacher")
        send_to_all = attrs.get("send_to_all", False)
        if not send_to_all and not teacher:
            raise serializers.ValidationError("Bitta o'qituvchini tanlang yoki \"Hammasiga\"ni belgilang.")
        if send_to_all and teacher:
            raise serializers.ValidationError("Bitta o'qituvchi va \"Hammasiga\"ni birga tanlab bo'lmaydi.")
        return attrs

    def create(self, validated_data):
        teacher = validated_data.pop("teacher", None)
        send_to_all = validated_data.pop("send_to_all", False)
        task = TeacherTask.objects.create(
            created_by=self.context["request"].user, is_broadcast=send_to_all, **validated_data
        )
        assign_task(task, teacher=teacher, send_to_all=send_to_all)
        return task


class TeacherTaskListSerializer(serializers.ModelSerializer):
    """Director's view of a task they sent — how many teachers got it, how many are done."""

    category_display = serializers.CharField(source="get_category_display", read_only=True)
    assignee_count = serializers.IntegerField(source="assignments.count", read_only=True)
    done_count = serializers.SerializerMethodField()

    class Meta:
        model = TeacherTask
        fields = (
            "id",
            "title",
            "description",
            "category",
            "category_display",
            "is_broadcast",
            "assignee_count",
            "done_count",
            "created_at",
        )

    def get_done_count(self, obj) -> int:
        return obj.assignments.filter(is_done=True).count()


class TeacherTaskAssignmentSerializer(serializers.ModelSerializer):
    """A teacher's own copy of an assigned task."""

    title = serializers.CharField(source="task.title", read_only=True)
    description = serializers.CharField(source="task.description", read_only=True)
    category = serializers.CharField(source="task.category", read_only=True)
    category_display = serializers.CharField(source="task.get_category_display", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TeacherTaskAssignment
        fields = (
            "id",
            "task",
            "title",
            "description",
            "category",
            "category_display",
            "created_by_name",
            "is_done",
            "completed_at",
            "created_at",
        )
        read_only_fields = ("id", "task", "is_done", "completed_at", "created_at")

    def get_created_by_name(self, obj) -> str:
        return str(obj.task.created_by) if obj.task.created_by else ""
