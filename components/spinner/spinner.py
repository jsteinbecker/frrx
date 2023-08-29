from django_components import component


@component.register("Spinner")
class SpinnerComponent(component.Component):

    template_name = "components/spinner/spinner.html"

    def get_context_data(self, **kwargs):
        htmx = kwargs.get("htmx", True)
        return {
            "htmx": htmx,
            "size": kwargs.get("size", "normal"),
            "color": kwargs.get("color", "text-white"),
            "classes": kwargs.get("classes", ""),
        }