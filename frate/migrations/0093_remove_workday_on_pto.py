# Generated by Django 4.1.7 on 2023-08-07 14:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0092_remove_slot_hours'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workday',
            name='on_pto',
        ),
    ]
