# Generated by Django 4.1.7 on 2023-08-29 02:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("frate", "0124_versionemployee_periods_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SolutionAttempt",
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
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "changed",
                    models.ManyToManyField(
                        related_name="solution_attempts", to="frate.slot"
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solution_attempts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solution_attempts",
                        to="frate.version",
                    ),
                ),
            ],
            options={
                "ordering": ["created"],
            },
        ),
    ]
