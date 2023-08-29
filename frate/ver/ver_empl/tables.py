from django.utils.html import format_html
from django_tables2 import tables, Column, CheckBoxColumn, A
from .models import VersionEmployee



class VersionEmployeeTable(tables.Table):

    action_select = CheckBoxColumn(accessor='pk', orderable=False)
    employee = Column(accessor='employee', orderable=False, verbose_name='Employee')
    hours = Column(accessor='hours', orderable=False, verbose_name='Hours')
    overtime = Column(accessor='overtime', orderable=False, verbose_name='Overtime')
    discrepancy = Column(accessor='discrepancy', orderable=False, verbose_name='Discrepancy')

    class Meta:
        model = VersionEmployee
        fields = ('action_select', 'name', 'hours', 'overtime', 'discrepancy')

        attrs = {'class': 'table table-striped table-hover table-sm table-bordered w-fit-content'}
        empty_text = 'No employees in this version.'



    @staticmethod
    def render_employee(self, record):
        return format_html(
            '<span><strong>{}</strong>{}</span>',
                    record.employee.initials + record.employee.initials_suffix,
                    record.employee.name
        )
