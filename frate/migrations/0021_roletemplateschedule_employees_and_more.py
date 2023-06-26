# Generated by Django 4.1.7 on 2023-06-17 03:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0020_remove_genericrtsslot_role_template_schedule_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='roletemplateschedule',
            name='employees',
            field=models.ManyToManyField(related_name='role_template_schedules', to='frate.employee'),
        ),
        migrations.CreateModel(
            name='RoleTemplateScheduleSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sd_id', models.PositiveSmallIntegerField()),
                ('type', models.CharField(choices=[('G', 'Generic'), ('O', 'Off'), ('D', 'Direct'), ('R', 'Rotating')], default='G', max_length=1)),
                ('shifts', models.ManyToManyField(related_name='role_template_slots', to='frate.shift')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='frate.roletemplateschedule')),
            ],
        ),
    ]
