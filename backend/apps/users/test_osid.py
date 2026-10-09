from django.test import TestCase

from apps.common.testing import make_student

from .models import User
from .services import generate_osid


class GenerateOsidTests(TestCase):
    def test_generate_osid_is_10_digits_no_leading_zero(self):
        osid = generate_osid()
        self.assertEqual(len(osid), 10)
        self.assertTrue(osid.isdigit())
        self.assertNotEqual(osid[0], "0")

    def test_generate_osid_retries_on_collision(self):
        existing = make_student()[0]
        taken = existing.osid
        self.assertIsNotNone(taken)

        # Force the first candidate to collide with an already-used osid, then
        # a free one — generate_osid must skip the taken value.
        free = "1234500000" if taken != "1234500000" else "1234500001"
        taken_int = int(taken) - 1_000_000_000
        free_int = int(free) - 1_000_000_000
        sequence = iter([taken_int, free_int])

        import apps.users.services as services

        original = services.secrets.randbelow
        services.secrets.randbelow = lambda _n: next(sequence)
        try:
            result = generate_osid()
        finally:
            services.secrets.randbelow = original

        self.assertEqual(result, free)


class UserOsidTests(TestCase):
    def test_new_user_gets_unique_osid(self):
        a = make_student()[0]
        b = make_student()[0]
        self.assertTrue(a.osid and b.osid)
        self.assertNotEqual(a.osid, b.osid)

    def test_osid_persists_and_is_not_regenerated_on_resave(self):
        user = make_student()[0]
        first = user.osid
        user.first_name = "Changed"
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.osid, first)

    def test_all_users_have_osid_after_backfill(self):
        # Every factory user already goes through save(); none should be null.
        self.assertFalse(User.objects.filter(osid__isnull=True).exists())


class OsidRetryExhaustionTests(TestCase):
    def test_save_raises_instead_of_saving_without_osid(self):
        from django.db import IntegrityError

        import apps.users.services as services

        taken = make_student()[0].osid
        original = services.generate_osid
        services.generate_osid = lambda: taken  # every draw collides (insert race)
        try:
            with self.assertRaises(IntegrityError):
                User.objects.create_user(
                    username="racer", email="racer@example.com", password="x"
                )
        finally:
            services.generate_osid = original
        self.assertFalse(User.objects.filter(email="racer@example.com").exists())
