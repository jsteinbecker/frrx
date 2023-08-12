from django.utils.html import format_html

from frate.models import Role
from django_tables2 import tables, TemplateColumn, LinkColumn, A, Column

from frate.sft.models import Shift


class RoleTable(tables.Table):
    name = LinkColumn('dept:role:detail', args=[A('department.slug'), A('slug')])
    shifts = Column('shifts', empty_values=(), orderable=False)

    class Meta:
        model = Role
        attrs = {'class': 'table text-xs table-fit table-auto'}
        fields = ('name', 'max_employees', 'employees', 'shifts',)


    def render_shifts(self, value, record):
        shifts = Shift.objects.filter(pk__in=record.shifts.all())
        html = "<div>{}</div>"
        inner = ""
        for shift in shifts:
            inner += f"<span class='badge w-fit'>{shift.name}</span>"
        return format_html(html.format(inner))

