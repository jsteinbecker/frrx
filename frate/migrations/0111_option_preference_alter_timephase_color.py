# Generated by Django 4.1.7 on 2023-08-15 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0110_alter_employee_options_timephase_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='preference',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='timephase',
            name='color',
            field=models.CharField(blank=True, choices=[('amber', 'Amber'), ('blue', 'Blue'), ('sky', 'Sky'), ('teal', 'Teal'), ('green', 'Green'), ('indigo', 'Indigo'), ('purple', 'Purple'), ('zinc', 'Gray')], max_length=20, null=True),
        ),
    ]
