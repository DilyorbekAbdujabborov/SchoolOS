from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import BridgeTokenAuthentication
from .models import Device
from .permissions import IsBridge
from .serializers import EventItemSerializer, HeartbeatSerializer
from .services import ingest_events


class _BridgeView(APIView):
    authentication_classes = [BridgeTokenAuthentication]
    permission_classes = [IsBridge]


class EventsView(_BridgeView):
    """Bridge uploads a batch of normalized terminal events."""

    def post(self, request):
        serializer = EventItemSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        result = ingest_events(request.bridge, serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)


class HeartbeatView(_BridgeView):
    """Bridge reports it (and its devices) are alive."""

    def post(self, request):
        serializer = HeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bridge = request.bridge
        bridge.last_seen_at = timezone.now()
        bridge.save(update_fields=["last_seen_at", "updated_at"])

        ip = request.META.get("REMOTE_ADDR")
        serials = serializer.validated_data["device_serials"]
        if ip and serials:
            Device.objects.filter(
                organization=bridge.organization, serial__in=serials
            ).update(last_known_ip=ip)

        return Response(status=status.HTTP_204_NO_CONTENT)
