# Generated by Django 4.1.7 on 2023-08-22 16:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("frate", "0116_alter_payperiod_goal"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payperiod",
            name="goal",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
