# Generated by Django 4.1.7 on 2023-07-08 01:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0062_workday_on_deck'),
    ]

    operations = [
        migrations.CreateModel(
            name='VersionScoreCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n_empty_slots', models.IntegerField(default=0)),
                ('version', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scorecard', to='frate.version')),
            ],
        ),
    ]
