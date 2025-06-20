from django.apps import AppConfig


class MembershipsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'memberships'

    def ready(self):
        import memberships.signals  # noqa: F401
