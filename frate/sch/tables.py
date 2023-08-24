from django.utils.html import format_html
from django_tables2 import tables, TemplateColumn, Column, LinkColumn, A

from frate.models import Slot, Version, Schedule, Role


# noinspection PyMethodMayBeStatic
class VersionTable(tables.Table):
    """Table for displaying versions."""
    n_filled        = Column(accessor='slots.filled.count', verbose_name='Filled')
    percent_filled  = Column(accessor='percent')
    is_best         = Column(accessor='is_best', verbose_name='Best')

    class Meta:
        model = Version
        fields = ('n', 'is_best', 'n_filled',  'percent_filled',)
        labels = {'n': 'Version #'}
        attrs = {'class': 'table table-striped table-hover text-xs table-auto table-bordered'}

    def render_percent_filled(self, value):
        return f'{value}%'

    def render_n(self, value):
        name = f'VERSION {value}'
        url = f'v/{value}'
        classes = 'text-xs text-indigo-300 hover:text-inidigo-500'
        return format_html('<a class="{}" href="{}">{}</a>', classes, url, name)

    def render_is_best(self, value):
        if value:
            classes = 'iconify-icon iconify-inline text-amber-400'
            icon = 'fluent:trophy-20-filled'
            span = '<span class="{}" data-icon="{}"></span>'.format(classes, icon)
            return format_html(span)
        else:
            return ''



class RoleListTable(tables.Table):
    """Tables for displaying the roles in a given schedule"""

    name = LinkColumn('dept:role:detail', args=[A('department.pk'), A('slug')], verbose_name='Role')

    class Meta:
        model = Role
        fields = ('name', 'employees')
        attrs = {'class': 'table table-striped table-hover text-xs table-auto'}

    @classmethod
    def render_employees(cls, value):
        html = ""
        for employee in value.all():
            html += f"<span class='badge w-fit'>{employee}</span>"
        return format_html(html)






