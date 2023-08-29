from django_components import component


@component.register("Switch")
class SwitchComponent(component.Component):

    template_name = "components/switch/switch.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["name"] = name
        context["value"] = value
        return context

    class Media:
        css = 'components/switch/switch.css'
        js  = 'components/switch/switch.js'


