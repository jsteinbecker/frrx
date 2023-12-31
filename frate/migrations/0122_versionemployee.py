# Generated by Django 4.1.7 on 2023-08-26 22:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("frate", "0121_delete_option"),
    ]

    operations = [
        migrations.CreateModel(
            name="VersionEmployee",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("per_period_goal", models.PositiveSmallIntegerField(default=0)),
                ("per_period_min", models.PositiveSmallIntegerField(default=0)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="frate.employee",
                    ),
                ),
                (
                    "version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="version_employees",
                        to="frate.schedule",
                    ),
                ),
            ],
        ),
    ]
