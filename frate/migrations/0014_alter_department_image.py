# Generated by Django 4.1.7 on 2023-06-15 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0013_alter_department_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='image',
            field=models.ImageField(blank=True, max_length=300, null=True, upload_to='img/'),
        ),
    ]
