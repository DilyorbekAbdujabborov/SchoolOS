from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import BridgeTokenAuthentication
from .models import Device
from .permissions import IsBridge
from .serializers import EventItemSerializer, HeartbeatSerializer
from .services import ingest_events
from .throttling import BridgeRateThrottle

#: Largest event batch one request may carry (spec §12: payload size limit).
MAX_EVENTS_PER_BATCH = 500


class _BridgeView(APIView):
    authentication_classes = [BridgeTokenAuthentication]
    permission_classes = [IsBridge]
    throttle_classes = [BridgeRateThrottle]


class EventsView(_BridgeView):
    """Bridge uploads a batch of normalized terminal events."""

    def post(self, request):
        if isinstance(request.data, list) and len(request.data) > MAX_EVENTS_PER_BATCH:
            raise serializers.ValidationError(
                {"detail": f"Bitta so'rovda {MAX_EVENTS_PER_BATCH} tadan ko'p event bo'lmasin."}
            )
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
