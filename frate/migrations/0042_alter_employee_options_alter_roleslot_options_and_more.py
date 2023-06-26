# Generated by Django 4.1.7 on 2023-06-25 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0041_alter_department_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='employee',
            options={'ordering': ['last_name', 'first_name']},
        ),
        migrations.AlterModelOptions(
            name='roleslot',
            options={'ordering': ['sd_id']},
        ),
        migrations.AlterModelOptions(
            name='shift',
            options={'ordering': ['start_time', 'name']},
        ),
        migrations.AddField(
            model_name='roleslot',
            name='employees',
            field=models.ManyToManyField(related_name='role_slots', to='frate.employee'),
        ),
        migrations.AlterField(
            model_name='department',
            name='image',
            field=models.FilePathField(blank=True, max_length=500, null=True, path='static/media/'),
        ),
    ]