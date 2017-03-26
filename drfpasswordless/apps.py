from django.apps import AppConfig


class DrfpasswordlessConfig(AppConfig):
    name = 'drfpasswordless'

    def ready(self):
        import drfpasswordless.signals  # NOQA
