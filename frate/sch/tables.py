from django.utils.html import format_html
from django_tables2 import tables, TemplateColumn, Column, LinkColumn, A

from frate.models import Slot, Version, Schedule


# noinspection PyMethodMayBeStatic
class VersionTable(tables.Table):
    """Table for displaying versions."""
    n_filled = Column(accessor='slots.filled.count', verbose_name='Filled')
    percent_filled = Column(accessor='percent')
    is_best = Column(accessor='is_best', verbose_name='Best')

    class Meta:
        model = Version
        fields = ('n', 'is_best', 'n_filled',  'percent_filled',)
        attrs = {'class': 'table table-striped table-hover text-xs table-auto'}

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


