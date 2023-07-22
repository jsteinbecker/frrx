# Generated by Django 4.1.7 on 2023-07-08 02:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0064_remove_versionscorecard_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='version',
            name='scorecard',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='version', to='frate.versionscorecard'),
        ),
    ]
