from pathlib import PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel

#: File extension → material kind, so the library can group and filter by type
#: without the uploader having to classify anything. Everything unknown is OTHER,
#: and a material with only a link is LINK.
_EXTENSION_KINDS = {
    "pdf": "PDF",
    "doc": "DOC", "docx": "DOC", "odt": "DOC", "rtf": "DOC", "txt": "DOC",
    "xls": "SHEET", "xlsx": "SHEET", "csv": "SHEET",
    "ppt": "SLIDES", "pptx": "SLIDES", "odp": "SLIDES",
    "jpg": "IMAGE", "jpeg": "IMAGE", "png": "IMAGE", "gif": "IMAGE",
    "webp": "IMAGE", "svg": "IMAGE", "heic": "IMAGE",
    "mp4": "VIDEO", "mov": "VIDEO", "avi": "VIDEO", "mkv": "VIDEO", "webm": "VIDEO",
    "mp3": "AUDIO", "wav": "AUDIO", "m4a": "AUDIO", "ogg": "AUDIO",
    "zip": "ARCHIVE", "rar": "ARCHIVE", "7z": "ARCHIVE",
}


class Material(TimeStampedModel):
    """One item in the school's materials library: a file to download or an
    external link, filed under a subject. Every student in the organization can
    see every material; teachers and the director upload them."""

    class Kind(models.TextChoices):
        LINK = "LINK", _("Link")
        PDF = "PDF", _("PDF")
        DOC = "DOC", _("Document")
        SHEET = "SHEET", _("Spreadsheet")
        SLIDES = "SLIDES", _("Presentation")
        IMAGE = "IMAGE", _("Image")
        VIDEO = "VIDEO", _("Video")
        AUDIO = "AUDIO", _("Audio")
        ARCHIVE = "ARCHIVE", _("Archive")
        OTHER = "OTHER", _("Other")

    organization = models.ForeignKey(
        "organizations.Organization",
        verbose_name=_("organization"),
        related_name="materials",
        on_delete=models.CASCADE,
    )
    subject = models.ForeignKey(
        "academics.Subject",
        verbose_name=_("subject"),
        related_name="materials",
        on_delete=models.PROTECT,
    )
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    file = models.FileField(_("file"), upload_to="materials/%Y/%m/", blank=True)
    link = models.URLField(_("link"), max_length=500, blank=True)
    kind = models.CharField(_("kind"), max_length=10, choices=Kind.choices, default=Kind.OTHER)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("uploaded by"),
        related_name="uploaded_materials",
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("material")
        verbose_name_plural = _("materials")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title

    def clean(self):
        if not self.file and not self.link:
            raise ValidationError(_("A material needs either a file or a link."))

    @staticmethod
    def derive_kind(file_name: str | None, link: str | None) -> str:
        if file_name:
            suffix = PurePosixPath(file_name).suffix.lower().lstrip(".")
            return _EXTENSION_KINDS.get(suffix, Material.Kind.OTHER)
        if link:
            return Material.Kind.LINK
        return Material.Kind.OTHER

    def save(self, *args, **kwargs):
        self.kind = self.derive_kind(self.file.name if self.file else None, self.link)
        super().save(*args, **kwargs)
