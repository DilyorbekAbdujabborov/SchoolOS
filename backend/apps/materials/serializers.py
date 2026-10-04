from pathlib import PurePosixPath

from rest_framework import serializers

from apps.academics.models import Subject

from .models import Material


class MaterialSerializer(serializers.ModelSerializer):
    """Read gives everything the library card needs (type, size, author); write
    takes a subject plus a file or a link, with the kind derived server-side."""

    file = serializers.FileField(write_only=True, required=False, allow_null=True)
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = (
            "id",
            "title",
            "description",
            "subject",
            "subject_name",
            "file",
            "file_url",
            "file_name",
            "file_size",
            "link",
            "kind",
            "kind_display",
            "uploaded_by_name",
            "created_at",
        )
        read_only_fields = ("kind", "created_at")

    def get_file_url(self, obj) -> str | None:
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_file_name(self, obj) -> str | None:
        return PurePosixPath(obj.file.name).name if obj.file else None

    def get_file_size(self, obj) -> int | None:
        if not obj.file:
            return None
        try:
            return obj.file.size
        except (OSError, ValueError):
            # File row kept but the blob is missing (e.g. cleared media) — don't
            # let a size lookup 500 the whole list.
            return None

    def get_uploaded_by_name(self, obj) -> str | None:
        user = obj.uploaded_by
        if not user:
            return None
        return user.get_full_name() or user.username

    def validate(self, attrs):
        # On create both may be absent; on update fall back to the instance.
        file = attrs.get("file", getattr(self.instance, "file", None))
        link = attrs.get("link", getattr(self.instance, "link", ""))
        if not file and not link:
            raise serializers.ValidationError(
                {"file": "Fayl yoki havola kiritilishi shart."}
            )
        return attrs
