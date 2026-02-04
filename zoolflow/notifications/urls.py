from django.urls import path
from .views import webhook_reciever

app_name = "notifications"
urlpatterns = [
    path(
        "mailgun-webhook/",
        webhook_reciever,
        name="webhook_receiver",
    ),
]
