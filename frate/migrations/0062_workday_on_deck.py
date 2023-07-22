# Generated by Django 4.1.7 on 2023-07-07 04:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0061_slot_streak_alter_department_pto_max_week_window_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workday',
            name='on_deck',
            field=models.ManyToManyField(blank=True, related_name='on_deck_days', to='frate.employee'),
        ),
    ]