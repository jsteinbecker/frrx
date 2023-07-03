# Generated by Django 4.1.7 on 2023-07-02 17:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0053_payperiod'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='slots', to='frate.payperiod'),
        ),
    ]