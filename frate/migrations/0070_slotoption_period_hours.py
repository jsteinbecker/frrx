# Generated by Django 4.1.7 on 2023-07-11 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0069_alter_payperiod_goal_alter_slot_period_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='slotoption',
            name='period_hours',
            field=models.IntegerField(blank=True, editable=False, null=True),
        ),
    ]
