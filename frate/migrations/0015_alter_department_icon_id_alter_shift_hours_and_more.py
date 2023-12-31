# Generated by Django 4.1.7 on 2023-06-15 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0014_alter_department_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='icon_id',
            field=models.CharField(blank=True, help_text='IconID (referenced via Iconify)', max_length=300, null=True, verbose_name='Icon'),
        ),
        migrations.AlterField(
            model_name='shift',
            name='hours',
            field=models.SmallIntegerField(default=10),
        ),
        migrations.AlterField(
            model_name='shift',
            name='weekdays',
            field=models.CharField(blank=True, choices=[('S', 'Sun'), ('M', 'Mon'), ('T', 'Tue'), ('W', 'Wed'), ('R', 'Thu'), ('F', 'Fri'), ('A', 'Sat')], max_length=7, null=True),
        ),
    ]
