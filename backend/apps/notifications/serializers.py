from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "title", "body", "category", "is_read", "created_at")
        read_only_fields = ("id", "title", "body", "category", "created_at")


class PushSubscriptionSerializer(serializers.Serializer):
    """Accepts a browser `PushSubscription.toJSON()` payload verbatim.

    The browser nests the crypto material under `keys`, so this validates that
    shape rather than mapping it onto the model's flat columns.
    """

    endpoint = serializers.URLField(max_length=500)
    keys = serializers.DictField(child=serializers.CharField())

    def validate_keys(self, value):
        if not value.get("p256dh") or not value.get("auth"):
            raise serializers.ValidationError("Both 'p256dh' and 'auth' keys are required.")
        return value
