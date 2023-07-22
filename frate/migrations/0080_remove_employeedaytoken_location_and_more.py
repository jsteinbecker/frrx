# Generated by Django 4.1.7 on 2023-07-17 23:06

from django.db import migrations, models
import django.db.models.deletion
import frate.validators


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0079_remove_preferredhoursguide_end_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employeedaytoken',
            name='location',
        ),
        migrations.AddField(
            model_name='employeedaytoken',
            name='position',
            field=models.CharField(default='DECK', max_length=10),
        ),
        migrations.AlterField(
            model_name='employeedaytoken',
            name='employee',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='tokens', to='frate.employee'),
        ),
        migrations.AlterField(
            model_name='employeedaytoken',
            name='workday',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='tokens', to='frate.workday'),
        ),
        migrations.AlterField(
            model_name='slot',
            name='direct_template',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='direct_template_for', to='frate.employee'),
        ),
        migrations.AlterField(
            model_name='slot',
            name='employee',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_active': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='slots', to='frate.employeedaytoken', validators=[frate.validators.SlotOvertimeValidator]),
        ),
        migrations.AlterField(
            model_name='slotoption',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='frate.employee'),
        ),
    ]
