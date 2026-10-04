"""Convert existing User.role values to lowercase.

`User.Role` moved from UPPERCASE to lowercase values (director/teacher/student)
so the stored role matches the `/app/<role>` route segment and the frontend's
Role union. The choices change is purely in Python; this migration rewrites the
rows that already hold the old values.
"""

from django.db import migrations

ROLE_MAP = {"DIRECTOR": "director", "TEACHER": "teacher", "STUDENT": "student"}


def to_lowercase(apps, schema_editor):
    User = apps.get_model("users", "User")
    for old, new in ROLE_MAP.items():
        User.objects.filter(role=old).update(role=new)


def to_uppercase(apps, schema_editor):
    User = apps.get_model("users", "User")
    for old, new in ROLE_MAP.items():
        User.objects.filter(role=new).update(role=old)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_studentprofile_address_studentprofile_gender_and_more"),
    ]

    operations = [
        migrations.RunPython(to_lowercase, to_uppercase),
    ]
