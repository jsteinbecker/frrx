from django.utils.html import format_html

from frate.models import Role
from django_tables2 import tables, TemplateColumn, LinkColumn, A, Column

from frate.sft.models import Shift


class RoleTable(tables.Table):
    name = LinkColumn('dept:role:detail', args=[A('department.slug'), A('slug')])
    shifts = Column('shifts', empty_values=(), orderable=False)
    open_positions = Column('Slots Open', empty_values=(), orderable=False)


    class Meta:
        model = Role
        attrs = {'class': 'table text-xs table-fit table-auto border border-gray-400'}
        fields = ('name', 'open_positions', 'employees', 'shifts',)


    @classmethod
    def render_shifts(cls, value, record):
        shifts = Shift.objects.filter(pk__in=record.shifts.all())
        html = "<div>{}</div>"
        inner = ""
        for shift in shifts:
            inner += f"<span class='badge w-fit'>{shift.name}</span>"
        return format_html(html.format(inner))

    @classmethod
    def render_open_positions(cls, value, record):
        n_open = record.max_employees - record.employees.count()
        if n_open == 0:
            n_open = ""
        html = "<div class='font-bold text-sky-300'>{}</div>"
        return format_html(html.format(n_open))
