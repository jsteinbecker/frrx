# Generated by Django 4.1.7 on 2023-07-11 07:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0070_slotoption_period_hours'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreferredHoursGuide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('hours', models.PositiveSmallIntegerField(default=0)),
                ('employee', models.ForeignKey(limit_choices_to={'fte__lt': 1}, on_delete=django.db.models.deletion.CASCADE, related_name='preferred_hours_guides', to='frate.employee')),
            ],
        ),
    ]
