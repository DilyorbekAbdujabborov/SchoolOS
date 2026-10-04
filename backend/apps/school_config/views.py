from typing import ClassVar

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsDirector, IsTeacher

from . import services
from .models import SchoolTimeSettings
from .serializers import ClassAccessStatusSerializer, SchoolTimeSettingsSerializer


class SchoolTimeSettingsView(RetrieveUpdateAPIView):
    """Anyone authenticated can read the school hours; only the director can change them."""

    serializer_class = SchoolTimeSettingsSerializer
    http_method_names = ("get", "patch")

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsDirector()]
        return [IsAuthenticated()]

    def get_object(self):
        user = self.request.user
        org = getattr(user, "active_organization", None)
        if org is None:
            raise ValueError("User has no active organization")
        return SchoolTimeSettings.get_solo(org)


class ClassAccessView(APIView):
    """Lets a teacher open the platform for their classes during a lesson, so
    students can use it despite the School Time Lock.

    - GET   → the current open/closed state of the teacher's classes.
    - POST  → open all of the teacher's classes until the end of the period.
    - DELETE → close them again early.
    """

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsTeacher]

    def get(self, request):
        status = services.teacher_access_status(request.user)
        return Response(ClassAccessStatusSerializer(status).data)

    def post(self, request):
        services.open_access_for_teacher(request.user)
        status = services.teacher_access_status(request.user)
        return Response(ClassAccessStatusSerializer(status).data)

    def delete(self, request):
        services.close_access_for_teacher(request.user)
        status = services.teacher_access_status(request.user)
        return Response(ClassAccessStatusSerializer(status).data)
