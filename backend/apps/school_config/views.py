from typing import ClassVar

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsDirector, IsDirectorOrReadOnly, IsOrgStaff

from . import services
from .models import SchoolDayException, SchoolTimeSettings
from .serializers import (
    ClassAccessStatusSerializer,
    SchoolDayExceptionSerializer,
    SchoolTimeSettingsSerializer,
)


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
    """Lets staff open the platform during a lesson, so students can use it
    despite the School Time Lock. A teacher opens their own classes; a director
    (or owner/admin) opens every class in the school.

    - GET    → the current open/closed state of the caller's classes.
    - POST   → open those classes until the end of the current period.
    - DELETE → close them again early.
    """

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsOrgStaff]

    def get(self, request):
        status = services.access_status(request.user)
        return Response(ClassAccessStatusSerializer(status).data)

    def post(self, request):
        services.open_access(request.user)
        status = services.access_status(request.user)
        return Response(ClassAccessStatusSerializer(status).data)

    def delete(self, request):
        services.close_access(request.user)
        status = services.access_status(request.user)
        return Response(ClassAccessStatusSerializer(status).data)


class SchoolDayExceptionViewSet(ModelViewSet):
    """Calendar overrides of the weekly school schedule (holidays, vacations and
    make-up working days). Any member may read them; only a director edits them.
    Always scoped to the caller's active organization."""

    serializer_class = SchoolDayExceptionSerializer
    permission_classes: ClassVar[list[type[BasePermission]]] = [IsDirectorOrReadOnly]

    def get_queryset(self):
        return SchoolDayException.objects.filter(
            organization_id=self.request.user.active_organization_id
        )

    def perform_create(self, serializer):
        serializer.save(organization_id=self.request.user.active_organization_id)
