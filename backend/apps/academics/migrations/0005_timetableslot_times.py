from datetime import date, datetime, timedelta

from django.db import migrations, models


def backfill_slot_times(apps, schema_editor):
    """Seed the new per-slot times from the old single global SchoolTimeSettings table.

    Slots are shift-aware now, but any pre-existing slot was created when the only
    source of truth was the global period table, so mirror that computation once.
    (Historical models carry no custom methods, hence the inlined arithmetic.)
    """
    TimetableSlot = apps.get_model("academics", "TimetableSlot")
    SchoolTimeSettings = apps.get_model("school_config", "SchoolTimeSettings")

    settings_obj = SchoolTimeSettings.objects.filter(pk=1).first()
    if settings_obj is None:
        return

    duration = settings_obj.period_duration_minutes
    short = settings_obj.short_break_minutes
    long = settings_obj.long_break_minutes
    after = settings_obj.long_break_after_period

    for slot in TimetableSlot.objects.filter(start_time__isnull=True).iterator():
        current = datetime.combine(date(2000, 1, 1), settings_obj.start_time)
        for period in range(1, slot.period_number):
            current += timedelta(minutes=duration)
            current += timedelta(minutes=long if period == after else short)
        slot.start_time = current.time()
        slot.end_time = (current + timedelta(minutes=duration)).time()
        slot.save(update_fields=["start_time", "end_time"])


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0004_lessonreminder"),
        ("school_config", "0002_schooltimesettings_long_break_after_period_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="timetableslot",
            name="start_time",
            field=models.TimeField(null=True, verbose_name="start time"),
        ),
        migrations.AddField(
            model_name="timetableslot",
            name="end_time",
            field=models.TimeField(null=True, verbose_name="end time"),
        ),
        migrations.RunPython(backfill_slot_times, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="timetableslot",
            name="start_time",
            field=models.TimeField(verbose_name="start time"),
        ),
        migrations.AlterField(
            model_name="timetableslot",
            name="end_time",
            field=models.TimeField(verbose_name="end time"),
        ),
        migrations.RemoveConstraint(
            model_name="timetableslot",
            name="unique_teacher_slot",
        ),
        migrations.AddConstraint(
            model_name="timetableslot",
            constraint=models.UniqueConstraint(
                fields=["teacher", "day_of_week", "start_time"],
                name="unique_teacher_slot",
            ),
        ),
    ]
