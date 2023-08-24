from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_tables2 import A, Column, LinkColumn, TemplateColumn, Table
from frate.models import PayPeriod, Employee, Version, Slot



class EmployeePayPeriodSummaryTable(Table):

    start_date = Column(verbose_name='Start Date')
    hours = Column(verbose_name='Hours')
    goal = Column(verbose_name='Goal')

    class Meta:
        model = PayPeriod
        fields = ('start_date', 'hours', 'goal')
        attrs = {'class': 'table table-striped table-bordered table-hover table-sm'}
        empty_text = 'No data available'


    def render_start_date(self, value, record):
        return record.start_date().strftime('%a %b %d')


    def render_hours(self, value, record):
        if value > record.goal:
            symbol = ("<i class='iconify-icon iconify-inline text-amber-400' "
                      "data-icon='ph:warning-circle-duotone' data-inline='true'></i>")
        else:
            symbol = ("<i class='iconify-icon iconify-inline text-green-500' "
                      "data-icon='ph:check-circle-duotone' data-inline='true'></i>")

        return format_html(f'<div class="flex flex-row"> {symbol} <div class="ml-2">{value} hr</div></div>')


    def render_goal(self, value, record):
        return f'{value} hr'
