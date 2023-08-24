from django_components import component


@component.register("Menu")
class Popover(component.Component):

    template_name = "components/menu/menu.html"

    def get_context_data(self, **kwargs):
        return {}



@component.register("MenuMainItem")
class MenuMainItem(component.Component):

    template_name = "components/menu/menu-main-item.html"

    def get_context_data(self, title, url, icon=None, warn=False, **kwargs):
        return {
            "title": title,
            "url": url,
            "icon": icon or "fa:fa-circle",
            "warn": warn,
        }


@component.register("MenuDropdown")
class MenuDropdown(component.Component):

    template_name = "components/menu/menu-dropdown.html"

    def get_context_data(self, title, **kwargs):
        return {"title": title}



@component.register("MenuItem")
class MenuItem(component.Component):

    template_name = "components/menu/menu-item.html"

    def get_context_data(self, title, url, icon=None, warn=False, **kwargs):
        return {
            "title": title,
            "url": url,
            "icon": icon or "fa:fa-circle",
            "warn": warn,
        }
