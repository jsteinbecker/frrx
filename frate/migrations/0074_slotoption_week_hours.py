# Generated by Django 4.1.7 on 2023-07-11 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0073_remove_slot_slot_type_slot_exceeds_streak_pref_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='slotoption',
            name='week_hours',
            field=models.IntegerField(blank=True, editable=False, null=True),
        ),
    ]