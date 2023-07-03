from django.apps import AppConfig


class FrateConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frate'
    
    def ready(self):
        from . import signals
        from frate.ver import signals
        from frate.payprd import signals






