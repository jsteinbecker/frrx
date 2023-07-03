from django import template
from django.template import Library

register = Library()



@register.filter(
    name='split')
def split(value: str, key  : str ) -> list:
    return value.split(key)

@register.filter(name='glue')
def glue(value, key) -> str:
    return f'{value} {key}'

@register.inclusion_tag(
    'tags/progress-bar.html',
    name='progress')
def progress_bar(value: int,max_ : int =100 ) -> dict:

    if value == '': value = 0
    if int(value) > int(max_):
        value = int(max_)
    return {'value': int(value), 'maximum': int(max_), 'width': value / max_ * 100 }


@register.simple_tag(
    name='checkAssigned')
def check_assigned(workday, shift) -> [str | None]:
    if workday.slots.filter(shift__isnull=False,shift=shift, employee__isnull=False).exists():
        return str(workday.slots.filter(shift=shift).first().employee.initials) or 'N/A'
    else:
        return None


@register.inclusion_tag('tags/checkmark.html', name='checkOption')
def check_option(employee, shift, workday) -> dict:
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
    # IS TRAINED # IS ACTIVE
    slot = workday.slots.filter(shift=shift, workday=workday).first()
    if slot.direct_template == employee:
        details['d-template'] = True
    else:
        details['d-template'] = False
    if employee.shifttraining_set.filter(shift=shift,is_active=True).exists():
        if workday.slots.filter(employee=employee).exclude(shift=shift).exists():
            details['on-day'] = True
        else:
            details['on-day'] = False

        details['assigned'] = True if workday.slots.filter(shift=shift, employee=employee).exists() else False
        details['template'] = employee.template_schedules.filter(shift=shift).exists()


@register.simple_tag(name='checkPtoBg')
def check_pto_bg(employee, day) -> str :

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
def check_tdo_bg(employee, day) -> str :

    if day.on_tdo.filter(pk=employee.pk).exists():
        return 'bg-warning-secondary'
    else:
        return ''


@register.filter(name='getColor')
def get_color(templ_slot_type, to_class='bg'):
    if templ_slot_type == 'G':
        return f'{to_class}-sky-600'
    elif templ_slot_type == 'R':
        return f'{to_class}-amber-600'
    elif templ_slot_type == 'O':
        return f'{to_class}-zinc-700 opacity-40'
    elif templ_slot_type == 'D':
        return f'{to_class}-indigo-400'



class ScriptTags:
    """
    ═════════════
     SCRIPT TAGS
    ═════════════
    :iconify_script: returns the script tag for iconify.
    :datepicker_script: returns the script tag for datepicker.
    :close_modal_script: returns the script tag for closing modals.
    :floating_ui_script: returns the script tag for floating ui.

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

    @staticmethod
    @register.inclusion_tag('tags/floating-ui-script.html', name='floatingUiScript')
    def floating_ui_script():
        return {}

    @staticmethod
    @register.inclusion_tag('tags/tooltip-init.html', name='tooltipInitScript')
    def tooltip_init_script():
        return {}


class Components:

    @staticmethod
    @register.inclusion_tag('widgets/icon-button.html', name='iconButton')
    def icon_button(icon: str,title: str = '',url : str = '') -> dict:
        return {'icon_id': icon, 'url': url, 'title': title}

    @staticmethod
    @register.inclusion_tag('widgets/icon-button-del.html', name='iconDelete')
    def icon_delete_button(icon: str,title: str = '',url : str = '') -> dict:
        return {'icon_id': icon, 'url': url, 'title': title}

    @staticmethod
    @register.inclusion_tag('widgets/icon-button-2.html', name='iconButton2')
    def icon_button_2(icon: str, title: str = '', url: str = '') -> dict:
        return {'icon_id': icon, 'url': url, 'title': title}

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
                'label': 'ADMIN'
            }
        ]
        return {'options': options}

    @staticmethod
    @register.inclusion_tag('widgets/backlink.html', name='backlink')
    def backlink(title,url):
        return {'title':title,'url':url}

    @staticmethod
    @register.inclusion_tag('widgets/documentation-link.html', name='doc')
    def documentation_link(title,url):
        return {'title':title,'url':url}

    @staticmethod
    @register.inclusion_tag('widgets/title-block.html', name='title')
    def title_block(title,subtitle,descriptor=None):
        return {'title':title,'subtitle':subtitle,'descriptor':descriptor}

    @staticmethod
    @register.inclusion_tag('widgets/stat.html', name='stat')
    def stat(fig_name, fig_value, description=""):
        return {'fig_name':fig_name,'fig_value':fig_value,'description':description}

    @staticmethod
    @register.inclusion_tag('widgets/label-group.html', name='labelGroup')
    def label_group(label, value):
        return {'label':label,'value':value}

    @staticmethod
    @register.inclusion_tag('widgets/dropdown-widget.html', name='dropdown')
    def dropdown(title,items):
        return {'title':title,'items':items}