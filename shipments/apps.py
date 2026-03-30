from django.apps import AppConfig


class ShipmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shipments"
    verbose_name = "Посилки"

    def ready(self):
        import shipments.signals