from django.forms import fields
from django.forms.utils import flatatt
from django.core.validators import EMPTY_VALUES



class SwitchInput(fields.CheckboxInput):

    def __init__(self, *args, **kwargs):
        self.switch_text = kwargs.pop('switch_text', None)
        super(SwitchInput, self).__init__(*args, **kwargs)

    def render(self, name, value=None, attrs=None, **kwargs):
        if value in EMPTY_VALUES:
            value = False
        final_attrs = self.build_attrs(attrs)
        if value:
            final_attrs['checked'] = 'checked'
        else:
            final_attrs['checked'] = ''
        if self.switch_text:
            final_attrs['data-switch-text'] = self.switch_text
        return u'<input%s />' % flatatt(final_attrs)


    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        if value in ('on', 'off'):
            return value == 'on'
        return value


    def widget_attrs(self, widget):
        attrs = super(SwitchInput, self).widget_attrs(widget)
        if self.switch_text:
            attrs['switch_text'] = self.switch_text
        return attrs


    class Media:
        css = 'components/switch/switch.css'
        js  = 'components/switch/switch.js'





