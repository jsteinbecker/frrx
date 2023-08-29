from django_components import component


@component.register("popover")
class Popover(component.Component):

    template_name = "components/popover/popover.html"

    def get_context_data(self, **kwargs):
        return {}
