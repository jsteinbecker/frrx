# Generated by Django 4.1.7 on 2023-08-28 23:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("frate", "0123_remove_versionemployee_per_period_goal_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="versionemployee",
            name="periods",
            field=models.ManyToManyField(
                related_name="version_employees", to="frate.payperiod"
            ),
        ),
        migrations.AlterField(
            model_name="versionemployee",
            name="employee",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="versions",
                to="frate.employee",
            ),
        ),
    ]
