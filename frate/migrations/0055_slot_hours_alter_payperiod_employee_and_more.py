# Generated by Django 4.1.7 on 2023-07-03 06:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0054_slot_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='hours',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='payperiod',
            name='employee',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='frate.employee'),
        ),
        migrations.AlterField(
            model_name='payperiod',
            name='pd_id',
            field=models.PositiveSmallIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='payperiod',
            name='version',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='frate.version'),
        ),
    ]
