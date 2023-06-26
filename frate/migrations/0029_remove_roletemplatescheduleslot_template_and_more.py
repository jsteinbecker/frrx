# Generated by Django 4.1.7 on 2023-06-21 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0028_roletemplateschedule_slug_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roletemplatescheduleslot',
            name='template',
        ),
        migrations.CreateModel(
            name='RoleLeaderSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sd_id', models.PositiveSmallIntegerField()),
                ('type', models.CharField(choices=[('G', 'Generic'), ('O', 'Off'), ('D', 'Direct'), ('R', 'Rotating')], default='G', max_length=1)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leader_slots', to='frate.roletemplateschedule')),
                ('shifts', models.ManyToManyField(related_name='leader_slots', to='frate.shift')),
            ],
        ),
        migrations.AddField(
            model_name='roletemplatescheduleslot',
            name='leader',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='frate.roleleaderslot'),
            preserve_default=False,
        ),
    ]