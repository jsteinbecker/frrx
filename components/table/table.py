from django_components import component


@component.register("customTable")
class CustomTable(component.Component):

    template_name = "components/table/table.html"

    def get_context_data(self, data, **kwargs):
        return {
            "actions": kwargs.get("actions", []),
            "data": data,
        }