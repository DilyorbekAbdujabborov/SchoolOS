from typing import ClassVar

from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, PushSubscription
from .serializers import NotificationSerializer, PushSubscriptionSerializer


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Every user only ever sees their own notifications."""

    serializer_class = NotificationSerializer
    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated]
    filterset_fields = ("category", "is_read")
    ordering_fields = ("created_at",)

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["patch"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
        return Response(self.get_serializer(notification).data)


class VapidPublicKeyView(APIView):
    """Hands the browser the public VAPID key it needs to subscribe to push."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated]

    def get(self, request):
        return Response({"public_key": getattr(settings, "VAPID_PUBLIC_KEY", "")})


class PushSubscribeView(APIView):
    """Stores (or refreshes) the caller's Web Push subscription.

    Keyed on the endpoint so re-subscribing the same browser updates its keys and
    re-points it at the current user instead of piling up duplicate rows.
    """

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated]

    def post(self, request):
        serializer = PushSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        PushSubscription.objects.update_or_create(
            endpoint=data["endpoint"],
            defaults={
                "user": request.user,
                "p256dh": data["keys"]["p256dh"],
                "auth": data["keys"]["auth"],
            },
        )
        return Response(status=status.HTTP_201_CREATED)


class PushUnsubscribeView(APIView):
    """Drops the caller's subscription for a given endpoint (on opt-out)."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get("endpoint")
        if endpoint:
            PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
