# Generated by Django 4.1.7 on 2023-07-02 10:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0051_role_description'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ptorequest',
            unique_together={('date', 'employee')},
        ),
    ]
