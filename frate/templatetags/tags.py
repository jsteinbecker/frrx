from django import template
from django.template import Library

register = Library()



@register.filter(name='split')
def split(value: str,
          key  : str
           ) -> list:
    return value.split(key)

@register.inclusion_tag('tags/progress-bar.html', name='progress')
def progress_bar(value: int,
                 max_ : int =100
                  ) -> dict:
    if value == '': value = 0
    if int(value) > int(max_):
        value = int(max_)
    return {'value': int(value), 'maximum': int(max_), 'width': value / max_ * 100 }

@register.simple_tag(name='checkAssigned')
def check_assigned(workday,
                   shift,
                   ) -> str | None:
    if workday.slots.filter(shift=shift, employee__isnull=False).exists():
        return workday.slots.filter(shift=shift).first().employee.initials
    else:
        return None




@register.inclusion_tag('tags/checkmark.html', name='checkOption')
def check_option(employee,
                 shift,
                 workday,
                 ) -> dict:
    """
    CHECK OPTION
    :returns dict:
                 ex {'status'  : 'available'|'deferent'|'unavailable',
                     'assigned': True|False }
    * available & assigned   -> 'shield'
    * available & unassigned -> 'check'
    * deferent               -> 'check' (faded)
    """
    details = {}

    if shift in employee.shifts.all():
        if workday.options.filter(employee=employee, slot__shift=shift, level__in=['P','A']).exists():
            details['status'] = 'available'
        elif workday.options.filter(employee=employee,slot__shift=shift, level='D').exists():
            details['status'] = 'deferent'
    else:
        details['status'] = 'unavailable'

    if workday.slots.filter(shift=shift,employee=employee).exists():
        details['assigned'] = True
    else:
        details['assigned'] = False

    details['shift'] = shift
    details['employee'] = employee
    return details


@register.simple_tag(name='checkPtoBg')
def check_pto_bg(employee,
                      day
                        ) -> str :
    from datetime import datetime
    if isinstance(day, datetime):
        date = datetime.strptime(day, '%Y-%m-%d').date()
    else:
        date = day.date
    if employee.pto_requests.filter(date=date).exists():
        return 'bg-warning'
    else:
        return ''

@register.simple_tag(name='checkTdoBg')
def check_tdo_bg(employee,
                      day
                        ) -> str :
    if day.on_tdo.filter(pk=employee.pk).exists():
        return 'bg-warning-secondary'
    else:
        return ''




class ScriptTags:
    """
    ═════════════
     SCRIPT TAGS
    ═════════════
    :method iconify_script: returns the script tag for iconify

    """

    @staticmethod
    @register.inclusion_tag('tags/iconify-script.html', name='iconifyScript')
    def iconify_script():
        return {}

    @staticmethod
    @register.inclusion_tag('tags/jquery-script.html', name='jQueryScript')
    def datepicker_script():
        return {}

    @staticmethod
    @register.inclusion_tag('tags/close-modal-script.html', name='closeModalScript')
    def close_modal_script():
        return {}


class Components:

    @staticmethod
    @register.inclusion_tag('widgets/date-select.html', name='calendarPicker')
    def calendar_picker(form_action: str = ''):
        from datetime import date
        return {'today': date.today(), 'form_action': form_action}

    @staticmethod
    @register.inclusion_tag('widgets/bottom-nav.html', name='bottomNav')
    def bottom_nav():
        options = [
            {
                'url': '/',
                'icon': 'mdi:home',
                'label': 'HOME'
            },
            {
                'url': '/department/cpht/schedule/',
                'icon': 'mdi:calendar-clock',
                'label': 'SCHEDULE'
            },
            {
                'url': '/admin/',
                'icon': 'mdi:settings',
                'label': 'Admin'
            }
        ]
        return {'options': options}
