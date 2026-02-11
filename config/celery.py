from celery import Celery
import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("zoolflow")

app.config_from_object("django.conf:settings", namespace="CELERY_")
app.autodiscover_tasks()

app.conf.update(
    CELERY_ALWAYS_EAGER=True,
)
