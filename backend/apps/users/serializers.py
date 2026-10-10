import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import StudentProfile, TeacherProfile

User = get_user_model()

# Handles that would shadow a frontend route, an API prefix, or just confuse —
# a user may never claim one of these as their public profile handle.
RESERVED_HANDLES = frozenset(
    {
        "admin",
        "api",
        "app",
        "assets",
        "auth",
        "director",
        "help",
        "login",
        "logout",
        "me",
        "media",
        "null",
        "p",
        "profile",
        "register",
        "settings",
        "static",
        "student",
        "support",
        "teacher",
        "undefined",
        "user",
        "users",
    }
)

HANDLE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,28}[a-z0-9]$")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "is_staff",
            "is_active",
            "date_joined",
        )
        read_only_fields = ("id", "role", "is_staff", "is_active", "date_joined")


class MeSerializer(serializers.ModelSerializer):
    total_xp = serializers.SerializerMethodField()
    capabilities = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    teacher_profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "must_change_password",
            "total_xp",
            "avatar_url",
            "teacher_profile_id",
            "handle",
            "is_profile_public",
            "capabilities",
        )
        read_only_fields = fields

    def get_capabilities(self, obj) -> dict:
        """The acting organization's client-config denials, so the frontend can
        hide sidebar entries, routes and buttons the API would refuse anyway."""
        from apps.organizations.capabilities import get_denied

        request = self.context.get("request")
        organization = getattr(request, "organization", None) or obj.active_organization
        if organization is None:
            return {"denied": []}
        return {"denied": sorted(get_denied(organization))}

    def get_total_xp(self, obj) -> int | None:
        profile = getattr(obj, "student_profile", None)
        return profile.total_xp if profile else None

    def get_teacher_profile_id(self, obj) -> int | None:
        """Lets the frontend filter `/timetable-slots/` and `/lessons/` down to a
        teacher's own taught periods — that queryset is scoped more broadly (it
        also includes a homeroom teacher's led-class slots taught by someone
        else), so a `teacher=<this id>` filter is the only reliable way to get
        just "my own schedule" for a linear, one-lesson-per-period day view."""
        profile = getattr(obj, "teacher_profile", None)
        return profile.id if profile else None

    def get_avatar_url(self, obj) -> str | None:
        if not obj.avatar:
            return None
        request = self.context.get("request")
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class ParentContactSerializer(serializers.ModelSerializer):
    """Lets a student self-report a parent's phone number — used only to help
    the parent find/confirm the right child when linking Telegram; the actual
    link still goes through a one-time code, never this number directly."""

    class Meta:
        model = StudentProfile
        fields = ("parent_phone_number",)


class PublicProfileSettingsSerializer(serializers.ModelSerializer):
    """Lets a user set their own public-profile handle and visibility.

    The handle is the `/p/<handle>/` slug, so it is normalised to lowercase,
    checked against a reserved-word list, and must be unique account-wide. An
    empty handle clears it (and the profile stops resolving)."""

    handle = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=30)

    class Meta:
        model = User
        fields = ("handle", "is_profile_public")

    def validate_handle(self, value):
        value = (value or "").strip().lower()
        if not value:
            return None
        if not HANDLE_RE.match(value):
            raise serializers.ValidationError(
                "Handle 2-30 ta belgidan iborat: faqat kichik harf, raqam va "
                "defis (boshida/oxirida defis bo'lmasin)."
            )
        if value in RESERVED_HANDLES:
            raise serializers.ValidationError("Bu handle band — boshqasini tanlang.")
        queryset = User.objects.filter(handle=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Bu handle allaqachon olingan.")
        return value

    def validate(self, attrs):
        # Can't go public without a handle — the profile would never resolve.
        wants_public = attrs.get("is_profile_public", getattr(self.instance, "is_profile_public", False))
        handle = attrs.get("handle", getattr(self.instance, "handle", None))
        if wants_public and not handle:
            raise serializers.ValidationError(
                {"handle": "Profilni ommaviy qilishdan oldin handle tanlang."}
            )
        return attrs


MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate_avatar(self, value):
        if value.size > MAX_AVATAR_SIZE_BYTES:
            raise serializers.ValidationError("Image must be 5MB or smaller.")
        return value


class TeacherSerializer(serializers.ModelSerializer):
    """Director-managed CRUD over a teacher's account + profile in one call."""

    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    is_active = serializers.BooleanField(source="user.is_active", required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = (
            "id",
            "user_id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "phone_number",
            "bio",
            "password",
        )

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.user_id)
        if queryset.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "Required when creating a teacher."})
        user = User.objects.create_user(
            username=user_data["email"],
            email=user_data["email"],
            password=password,
            role=User.Role.TEACHER,
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
        )
        return TeacherProfile.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        password = validated_data.pop("password", None)
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        if password:
            instance.user.set_password(password)
        instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class StudentSerializer(serializers.ModelSerializer):
    """Director-managed CRUD over a student's account + profile in one call."""

    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    is_active = serializers.BooleanField(source="user.is_active", required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    school_class_name = serializers.CharField(source="school_class.name", read_only=True)
    # PINFL is unique but optional: a blank value must become NULL, not "",
    # or a second blank-PINFL student would trip the unique constraint.
    pinfl = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=14)

    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = StudentProfile
        fields = (
            "id",
            "user_id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "school_class",
            "school_class_name",
            "pinfl",
            "passport_number",
            "middle_name",
            "gender",
            "address",
            "region",
            "birth_date",
            "phone_number",
            "parent_phone_number",
            "password",
            "total_xp",
        )
        read_only_fields = ("total_xp",)

    def validate_pinfl(self, value):
        value = (value or "").strip()
        if not value:
            return None
        if not (value.isdigit() and len(value) == 14):
            raise serializers.ValidationError("PINFL 14 ta raqamdan iborat bo'lishi kerak.")
        queryset = StudentProfile.objects.filter(pinfl=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Bu PINFL allaqachon ro'yxatda.")
        return value

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.user_id)
        if queryset.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "Required when creating a student."})
        user = User.objects.create_user(
            username=user_data["email"],
            email=user_data["email"],
            password=password,
            role=User.Role.STUDENT,
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
        )
        return StudentProfile.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        password = validated_data.pop("password", None)
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        if password:
            instance.user.set_password(password)
        instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
