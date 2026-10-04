from rest_framework import serializers

from .models import DemoRequest


class DemoRequestSerializer(serializers.ModelSerializer):
    """Public create-only serializer for a landing-page demo request.

    Only the visitor-supplied fields are writable; `status` is managed by the
    SchoolOS team in the admin, never set by the caller.
    """

    class Meta:
        model = DemoRequest
        fields = ("id", "name", "phone", "school_name", "message", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Ismni to'liq kiriting.")
        return value

    def validate_phone(self, value: str) -> str:
        value = value.strip()
        digits = sum(ch.isdigit() for ch in value)
        if digits < 7:
            raise serializers.ValidationError("Telefon raqamni to'g'ri kiriting.")
        return value
