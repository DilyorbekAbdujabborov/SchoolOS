from typing import ClassVar

from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsDirector

from .models import TeacherTask, TeacherTaskAssignment
from .serializers import (
    TeacherTaskAssignmentSerializer,
    TeacherTaskListSerializer,
    TeacherTaskWriteSerializer,
)


class TeacherTaskViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Director-only: send a task to one teacher or to all of them, and track it."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsDirector]

    def get_queryset(self):
        return (
            TeacherTask.objects.filter(created_by=self.request.user)
            .prefetch_related("assignments")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return TeacherTaskWriteSerializer
        return TeacherTaskListSerializer


class TeacherTaskAssignmentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """A teacher's own assigned tasks, with a way to mark one done."""

    serializer_class = TeacherTaskAssignmentSerializer
    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated]

    def get_queryset(self):
        profile = getattr(self.request.user, "teacher_profile", None)
        if not profile:
            return TeacherTaskAssignment.objects.none()
        return TeacherTaskAssignment.objects.filter(teacher=profile).select_related("task", "task__created_by")

    @action(detail=True, methods=["patch"], url_path="mark-done")
    def mark_done(self, request, pk=None):
        assignment = self.get_object()
        assignment.is_done = True
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=["is_done", "completed_at", "updated_at"])
        return Response(self.get_serializer(assignment).data)
