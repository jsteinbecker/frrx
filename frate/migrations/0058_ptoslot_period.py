# Generated by Django 4.1.7 on 2023-07-03 08:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0057_ptoslot'),
    ]

    operations = [
        migrations.AddField(
            model_name='ptoslot',
            name='period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pto_slots', to='frate.payperiod'),
        ),
    ]
