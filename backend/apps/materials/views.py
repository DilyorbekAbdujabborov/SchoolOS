from typing import ClassVar

from rest_framework import viewsets
from rest_framework.permissions import BasePermission

from apps.common.permissions import IsStaffOrReadOnly

from .models import Material
from .serializers import MaterialSerializer


class MaterialViewSet(viewsets.ModelViewSet):
    """The school's materials library. Every member of the organization can read
    it; teachers and the director upload, and each may remove their own (the
    director, anyone's). Scoped to the caller's active organization."""

    serializer_class = MaterialSerializer
    permission_classes: ClassVar[list[type[BasePermission]]] = [IsStaffOrReadOnly]
    filterset_fields: ClassVar[tuple[str, ...]] = ("subject", "kind", "uploaded_by")
    search_fields: ClassVar[tuple[str, ...]] = ("title", "description")
    ordering_fields: ClassVar[tuple[str, ...]] = ("created_at", "title")

    def get_queryset(self):
        return Material.objects.filter(
            organization_id=self.request.user.active_organization_id
        ).select_related("subject", "uploaded_by")

    def perform_create(self, serializer):
        serializer.save(
            organization_id=self.request.user.active_organization_id,
            uploaded_by=self.request.user,
        )
