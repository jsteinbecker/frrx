# Generated by Django 4.1.7 on 2023-08-09 05:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0097_shift_relative_rank'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='preference_score',
            field=models.FloatField(default=0.0),
        ),
    ]