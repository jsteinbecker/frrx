from django_components import component
import uuid


@component.register("SelectOne")
class SelectOne(component.Component):

    template_name = "components/selectone/selectone.html"


    def get_context_data(self, **kwargs):
        input_id = uuid.uuid4()
        return {
            "name": input_id,
        }

    class Media:
        js = "components/selectone/selectone.js"



@component.register("SelectOneOption")
class SelectOneOption(component.Component):

    template_name = "components/selectone/selectone-option.html"

    def get_context_data(self, value=None, label=None, selected=False, disabled=False, **kwargs):
        return {
            "value": value,
            "label": label,
            "selected": selected,
            "disabled": disabled
        }

    class Media:
        css = "components/selectone/selectone.css"
