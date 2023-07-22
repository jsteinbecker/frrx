# Generated by Django 4.1.7 on 2023-06-11 23:51

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('name', models.CharField(max_length=70)),
                ('slug', models.SlugField(max_length=70, primary_key=True, serialize=False, unique=True)),
                ('verbose_name', models.CharField(max_length=300)),
                ('schedule_week_length', models.PositiveSmallIntegerField(default=6)),
                ('initial_start_date', models.DateField(default='2023-02-05')),
                ('icon_id', models.CharField(blank=True, max_length=300, null=True)),
                ('img_url', models.CharField(blank=True, max_length=400, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('name', models.CharField(max_length=70)),
                ('slug', models.SlugField(max_length=70, primary_key=True, serialize=False, unique=True)),
                ('first_name', models.CharField(max_length=70)),
                ('last_name', models.CharField(max_length=70)),
                ('initials', models.CharField(max_length=10)),
                ('icon_id', models.CharField(blank=True, max_length=300, null=True)),
                ('start_date', models.DateField(default='2023-02-05')),
                ('is_active', models.BooleanField(default=True)),
                ('fte', models.FloatField(default=1.0, validators=[django.core.validators.MaxValueValidator(1.0), django.core.validators.MinValueValidator(0.0)])),
                ('pto_hours', models.SmallIntegerField(default=0)),
                ('template_week_count', models.PositiveSmallIntegerField(default=2)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='frate.department')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('name', models.CharField(max_length=70)),
                ('slug', models.SlugField(max_length=70, primary_key=True, serialize=False, unique=True)),
                ('verbose_name', models.CharField(max_length=300)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('year', models.PositiveSmallIntegerField()),
                ('n', models.PositiveSmallIntegerField()),
                ('slug', models.SlugField(max_length=300)),
                ('percent', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('D', 'Draft'), ('P', 'Published'), ('A', 'Archived')], default='D', max_length=1)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='frate.department')),
            ],
            options={
                'ordering': ['start_date'],
                'unique_together': {('department', 'slug'), ('department', 'year', 'n')},
            },
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('name', models.CharField(max_length=70)),
                ('slug', models.SlugField(max_length=70, primary_key=True, serialize=False, unique=True)),
                ('verbose_name', models.CharField(max_length=300)),
                ('start_time', models.TimeField()),
                ('hours', models.SmallIntegerField()),
                ('weekdays', models.CharField(choices=[('S', 'Sun'), ('M', 'Mon'), ('T', 'Tue'), ('W', 'Wed'), ('R', 'Thu'), ('F', 'Fri'), ('A', 'Sat')], default='SMTWRFA', max_length=7)),
                ('on_holidays', models.BooleanField(default=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shifts', to='frate.department')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='frate.shift')),
            ],
            options={
                'ordering': ['shift'],
            },
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n', models.PositiveSmallIntegerField()),
                ('status', models.CharField(choices=[('D', 'Draft'), ('P', 'Published'), ('A', 'Archived')], default='D', max_length=1)),
                ('percent', models.IntegerField(default=0)),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='frate.schedule')),
            ],
            options={
                'ordering': ['n', 'status'],
            },
        ),
        migrations.CreateModel(
            name='Workday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('weekday', models.CharField(blank=True, choices=[('S', 'Sun'), ('M', 'Mon'), ('T', 'Tue'), ('W', 'Wed'), ('R', 'Thu'), ('F', 'Fri'), ('A', 'Sat')], max_length=1, null=True)),
                ('sd_id', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('wk_id', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('pd_id', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('is_holiday', models.BooleanField(default=False)),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workdays', to='frate.version')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='TimePhase',
            fields=[
                ('name', models.CharField(max_length=70)),
                ('slug', models.SlugField(max_length=70, primary_key=True, serialize=False, unique=True)),
                ('verbose_name', models.CharField(max_length=300)),
                ('end_time', models.TimeField()),
                ('rank', models.PositiveSmallIntegerField()),
                ('icon_id', models.CharField(blank=True, max_length=300, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phases', to='frate.organization')),
            ],
            options={
                'ordering': ['end_time'],
            },
        ),
        migrations.CreateModel(
            name='TdoSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='frate.version')),
                ('workday', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='frate.workday')),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='SlotOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='frate.employee')),
                ('slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='frate.slot')),
            ],
        ),
        migrations.AddField(
            model_name='slot',
            name='version',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='frate.version'),
        ),
        migrations.AddField(
            model_name='slot',
            name='workday',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='frate.workday'),
        ),
        migrations.CreateModel(
            name='ShiftTraining',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effective_date', models.DateField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='frate.employee')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='frate.shift')),
            ],
        ),
        migrations.AddField(
            model_name='shift',
            name='phase',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shifts', to='frate.timephase'),
        ),
        migrations.CreateModel(
            name='PtoSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='frate.version')),
                ('workday', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='frate.workday')),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='EmployeeTemplateSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive')], default='A', max_length=1)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='template_schedules', to='frate.employee')),
            ],
            options={
                'ordering': ['employee', 'status'],
            },
        ),
        migrations.AddField(
            model_name='employee',
            name='shifts',
            field=models.ManyToManyField(related_name='employees', through='frate.ShiftTraining', to='frate.shift'),
        ),
        migrations.AddField(
            model_name='department',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='departments', to='frate.organization'),
        ),
        migrations.CreateModel(
            name='BaseTemplateSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sd_id', models.PositiveSmallIntegerField()),
                ('type', models.CharField(choices=[('D', 'Direct'), ('R', 'Rotating'), ('G', 'Generic'), ('O', 'Off')], default='D', max_length=1)),
                ('direct_shift', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='direct_template_slots', to='frate.shift')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='template_slots', to='frate.employee')),
                ('following', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='followers', to='frate.basetemplateslot')),
                ('rotating_shifts', models.ManyToManyField(related_name='rotating_template_slots', to='frate.shift')),
                ('template_schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='template_slots', to='frate.employeetemplateschedule')),
            ],
            options={
                'ordering': ['sd_id'],
            },
        ),
    ]
