# Generated by Django 4.1.7 on 2023-07-11 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0066_remove_version_scorecard_versionscorecard_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='allowed_as_streak_breakpoint',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
