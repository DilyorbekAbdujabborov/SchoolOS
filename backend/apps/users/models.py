from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

#: Uzbek national ID (PINFL/JSHSHIR) — exactly 14 digits.
pinfl_validator = RegexValidator(r"^\d{14}$", _("PINFL 14 ta raqamdan iborat bo'lishi kerak."))

# No import cycle: apps.organizations.models refers to the user model by
# `settings.AUTH_USER_MODEL` string and never imports apps.users.
from apps.organizations.models import OrganizationMembership


class UserManager(DjangoUserManager):
    """`createsuperuser` always creates a director account."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.DIRECTOR)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        # Stored lowercase so the value matches the `/app/<role>` route segment
        # and the frontend's Role union without a .toLowerCase() dance.
        DIRECTOR = "director", _("Director")
        TEACHER = "teacher", _("Teacher")
        STUDENT = "student", _("Student")

    email = models.EmailField(
        _("email address"),
        unique=True,
        help_text=_("Required. A unique email address."),
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    must_change_password = models.BooleanField(
        _("must change password"),
        default=False,
        help_text=_("Set when a temporary password was issued (e.g. bulk import)."),
    )
    avatar = models.ImageField(_("avatar"), upload_to="avatars/", null=True, blank=True)
    handle = models.SlugField(
        _("handle"),
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Ommaviy profil manzili: /p/<handle>/. Bo'sh bo'lsa profil ochilmaydi."),
    )
    is_profile_public = models.BooleanField(
        _("public profile"),
        default=False,
        help_text=_("Yoqilsa, handle orqali profil hamma uchun ochiq bo'ladi."),
    )
    osid = models.CharField(
        _("OSID"),
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        help_text=_(
            "10 xonali barqaror identifikator. Tashqi tizimlar (yuz terminali, "
            "uzedu) odamni shu kalit orqali bog'laydi. Avtomatik beriladi."
        ),
    )
    active_organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("active organization"),
        related_name="active_users",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_(
            "Which organization this user is currently working in. NULL means the "
            "user has no membership yet and the platform falls back to their only "
            "membership, or to no organization at all."
        ),
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering: ClassVar[list[str]] = ["-date_joined"]

    def save(self, *args, **kwargs):
        # Assign an OSID on first save. The generator already skips taken values;
        # the atomic retry here closes the insert race between two concurrent
        # creates drawing the same candidate.
        if not self.osid:
            from django.db import IntegrityError, transaction

            from .services import generate_osid

            last_error = None
            for _attempt in range(5):
                self.osid = generate_osid()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError as exc:
                    self.osid = None
                    last_error = exc
            # Never fall through to saving without an OSID — a user the terminals
            # can't match is worse than a failed create.
            raise last_error
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} <{self.email}>"

    def get_active_membership(self):
        """The membership that authorizes this request, or None.

        Resolution order:
          1. `active_organization`, if it is still an ACTIVE membership
          2. the user's single membership, if they only have one
          3. otherwise None — the caller must pick a switch target

        Never falls back to "any membership": with two organizations on the
        same account, guessing would hand the user the wrong permissions.
        """
        if not self.is_authenticated:
            return None

        if self.active_organization_id:
            membership = self.organization_memberships.filter(
                organization_id=self.active_organization_id,
                status=OrganizationMembership.Status.ACTIVE,
            ).first()
            if membership is not None:
                return membership

        memberships = self.organization_memberships.filter(
            status=OrganizationMembership.Status.ACTIVE
        ).order_by("organization_id")
        if len(memberships) == 1:
            return memberships[0]
        return None

    @property
    def active_membership(self):
        cached = getattr(self, "_active_membership_cache", None)
        if cached is not None:
            return cached
        membership = self.get_active_membership()
        self._active_membership_cache = membership
        return membership

    @property
    def active_role(self) -> str | None:
        """The role to authorize this user with, inside the active organization.

        This — not `self.role` — is what access control must use. `User.role`
        stays as a denormalized "primary role" for the current single-school
        deployment and for the login defaults.
        """
        membership = self.active_membership
        return membership.role if membership is not None else None

    @property
    def is_director(self) -> bool:
        return self.role == self.Role.DIRECTOR

    @property
    def is_teacher(self) -> bool:
        return self.role == self.Role.TEACHER

    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT

    @property
    def is_org_director(self) -> bool:
        return self.active_role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.DIRECTOR,
        )

    @property
    def is_org_teacher(self) -> bool:
        return self.active_role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.DIRECTOR,
            OrganizationMembership.Role.TEACHER,
            OrganizationMembership.Role.COACH,
        )

    @property
    def is_org_student(self) -> bool:
        return self.active_role in (
            OrganizationMembership.Role.STUDENT,
            OrganizationMembership.Role.MEMBER,
        )


class TeacherProfile(models.Model):
    """Extra data for users with role=TEACHER."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True)
    bio = models.TextField(_("bio"), blank=True)

    class Meta:
        verbose_name = _("teacher profile")
        verbose_name_plural = _("teacher profiles")

    def __str__(self) -> str:
        return str(self.user)


class StudentProfile(models.Model):
    """Extra data for users with role=STUDENT.

    The identity fields (PINFL, passport, middle name, gender, address, region)
    mirror the national IT-City/`digital.uz` person registry, so a student can
    be matched to or imported from that source without reshaping the data.
    """

    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    school_class = models.ForeignKey(
        "schools.SchoolClass",
        verbose_name=_("class"),
        related_name="students",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    pinfl = models.CharField(
        _("PINFL"),
        max_length=14,
        null=True,
        blank=True,
        unique=True,
        validators=[pinfl_validator],
        help_text=_("Jismoniy shaxsning identifikatsiya raqami (14 raqam)."),
    )
    passport_number = models.CharField(_("passport number"), max_length=20, blank=True)
    middle_name = models.CharField(_("middle name"), max_length=150, blank=True)
    gender = models.CharField(_("gender"), max_length=10, choices=Gender.choices, blank=True)
    address = models.CharField(_("address"), max_length=255, blank=True)
    region = models.CharField(_("region"), max_length=120, blank=True)
    birth_date = models.DateField(_("birth date"), null=True, blank=True)
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True)
    parent_phone_number = models.CharField(_("parent phone number"), max_length=20, blank=True)
    total_xp = models.PositiveIntegerField(
        _("total XP"),
        default=0,
        help_text=_("Never edit directly — only apps.gamification.services.award_xp may change this."),
    )

    class Meta:
        verbose_name = _("student profile")
        verbose_name_plural = _("student profiles")

    def __str__(self) -> str:
        return str(self.user)
