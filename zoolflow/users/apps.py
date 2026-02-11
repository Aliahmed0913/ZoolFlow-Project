from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zoolflow.users"

    def ready(self):
        import zoolflow.users.signals
