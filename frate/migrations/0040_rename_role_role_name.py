# Generated by Django 4.1.7 on 2023-06-22 09:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0039_employee_streak_pref_alter_role_department_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='role',
            old_name='role',
            new_name='name',
        ),
    ]