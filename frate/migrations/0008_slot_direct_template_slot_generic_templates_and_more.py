# Generated by Django 4.1.7 on 2023-06-14 06:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frate', '0007_alter_slotoption_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='direct_template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='direct_template_for', to='frate.employee'),
        ),
        migrations.AddField(
            model_name='slot',
            name='generic_templates',
            field=models.ManyToManyField(blank=True, related_name='generic_template_for', to='frate.employee'),
        ),
        migrations.AddField(
            model_name='slot',
            name='rotating_templates',
            field=models.ManyToManyField(blank=True, related_name='rotating_template_for', to='frate.employee'),
        ),
        migrations.AddField(
            model_name='workday',
            name='on_pto',
            field=models.ManyToManyField(blank=True, related_name='pto_days', to='frate.employee'),
        ),
        migrations.AddField(
            model_name='workday',
            name='templated_off',
            field=models.ManyToManyField(blank=True, related_name='templated_off_days', to='frate.employee'),
        ),
        migrations.AlterField(
            model_name='basetemplateslot',
            name='type',
            field=models.CharField(choices=[('D', 'Direct'), ('R', 'Rotating'), ('G', 'Generic'), ('O', 'Templated Off')], default='D', max_length=1),
        ),
    ]