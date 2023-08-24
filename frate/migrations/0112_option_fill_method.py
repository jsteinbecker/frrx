# Generated by Django 4.1.7 on 2023-08-15 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0111_option_preference_alter_timephase_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='fill_method',
            field=models.CharField(choices=[('P', 'Pick Up'), ('T', 'Trade'), ('O', 'Pick Up Into Overtime')], default='P', max_length=1),
        ),
    ]