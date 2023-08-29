from django.apps import AppConfig


class OptionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "frate.options"

    def ready(self):
        from .signals import option_self_update



