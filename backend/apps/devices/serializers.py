from rest_framework import serializers

from .models import AccessEvent


class EventItemSerializer(serializers.Serializer):
    device_serial = serializers.CharField(max_length=120)
    osid = serializers.CharField(max_length=64)
    event_time = serializers.DateTimeField()
    direction = serializers.ChoiceField(
        choices=AccessEvent.Direction.choices,
        default=AccessEvent.Direction.UNKNOWN,
    )
    verify_mode = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    raw = serializers.JSONField(required=False, default=dict)


class HeartbeatSerializer(serializers.Serializer):
    device_serials = serializers.ListField(
        child=serializers.CharField(max_length=120), required=False, default=list
    )
