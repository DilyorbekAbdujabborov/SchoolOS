from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from apps.common.testing import (
    default_organization,
    make_director,
    make_organization,
    make_student,
    make_subject,
    make_teacher,
)

from .models import Material


class MaterialModelTests(APITestCase):
    def test_kind_derived_from_file_extension(self):
        self.assertEqual(Material.derive_kind("notes.pdf", ""), "PDF")
        self.assertEqual(Material.derive_kind("slaydlar.pptx", ""), "SLIDES")
        self.assertEqual(Material.derive_kind("rasm.PNG", ""), "IMAGE")
        self.assertEqual(Material.derive_kind("arxiv.xyz", ""), "OTHER")

    def test_kind_link_when_no_file(self):
        self.assertEqual(Material.derive_kind(None, "https://youtu.be/abc"), "LINK")


class MaterialAPITests(APITestCase):
    def setUp(self):
        self.org = default_organization()
        self.subject = make_subject("Matematika")
        self.teacher_user, _ = make_teacher()
        self.director = make_director()
        self.student_user, _ = make_student()

    def _client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_student_can_list_materials(self):
        Material.objects.create(
            organization=self.org, subject=self.subject, title="Darslik", link="https://x.uz"
        )
        res = self._client(self.student_user).get(reverse("material-list"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)

    def test_student_cannot_create(self):
        res = self._client(self.student_user).post(
            reverse("material-list"),
            {"title": "x", "subject": self.subject.id, "link": "https://x.uz"},
        )
        self.assertEqual(res.status_code, 403)

    def test_teacher_can_create_with_link(self):
        res = self._client(self.teacher_user).post(
            reverse("material-list"),
            {"title": "Video dars", "subject": self.subject.id, "link": "https://youtu.be/x"},
        )
        self.assertEqual(res.status_code, 201)
        material = Material.objects.get()
        self.assertEqual(material.kind, "LINK")
        self.assertEqual(material.uploaded_by, self.teacher_user)
        self.assertEqual(material.organization, self.org)

    def test_teacher_can_upload_a_file(self):
        upload = SimpleUploadedFile("qollanma.pdf", b"%PDF-1.4 fake", content_type="application/pdf")
        res = self._client(self.teacher_user).post(
            reverse("material-list"),
            {"title": "Qo'llanma", "subject": self.subject.id, "file": upload},
            format="multipart",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Material.objects.get().kind, "PDF")

    def test_create_requires_file_or_link(self):
        res = self._client(self.teacher_user).post(
            reverse("material-list"),
            {"title": "Bo'sh", "subject": self.subject.id},
        )
        self.assertEqual(res.status_code, 400)

    def test_queryset_scoped_to_organization(self):
        other_org = make_organization()
        Material.objects.create(
            organization=other_org, subject=self.subject, title="Begona", link="https://x.uz"
        )
        Material.objects.create(
            organization=self.org, subject=self.subject, title="Meniki", link="https://y.uz"
        )
        res = self._client(self.student_user).get(reverse("material-list"))
        titles = [row["title"] for row in res.data["results"]]
        self.assertEqual(titles, ["Meniki"])

    def test_teacher_cannot_delete_another_teachers_material(self):
        other_teacher, _ = make_teacher()
        material = Material.objects.create(
            organization=self.org,
            subject=self.subject,
            title="Boshqa o'qituvchiniki",
            link="https://x.uz",
            uploaded_by=other_teacher,
        )
        res = self._client(self.teacher_user).delete(reverse("material-detail", args=[material.id]))
        self.assertEqual(res.status_code, 403)

    def test_director_can_delete_any_material(self):
        material = Material.objects.create(
            organization=self.org,
            subject=self.subject,
            title="O'qituvchiniki",
            link="https://x.uz",
            uploaded_by=self.teacher_user,
        )
        res = self._client(self.director).delete(reverse("material-detail", args=[material.id]))
        self.assertEqual(res.status_code, 204)
