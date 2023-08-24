from django_components import component


@component.register("ddFilter")
class DropDownFilter(component.Component):

    template_name = "components/ddfilter/ddfilter.html"
    empty_text = "No data available"

    def get_context_data(self, name, choices, **kwargs):
        return {
            "name": name,
            "choices": choices,
        }
