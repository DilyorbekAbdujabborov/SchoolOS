from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('duels', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='duelrating',
            name='rating',
            field=models.PositiveIntegerField(default=1000, verbose_name='rating'),
        ),
    ]