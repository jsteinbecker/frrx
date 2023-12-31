# Generated by Django 4.1.7 on 2023-06-13 02:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0003_remove_tdoslot_version_remove_tdoslot_workday_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='slot',
            unique_together={('workday', 'shift'), ('workday', 'employee')},
        ),
        migrations.CreateModel(
            name='PtoRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('status', models.CharField(choices=[('P', 'Pending'), ('A', 'Approved'), ('D', 'Denied')], default='P', max_length=1)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pto_requests', to='frate.employee')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
    ]
