from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services.webhook import verify_mailgun_hmac
from .services.trackers import UpdateEmailEventTracker
from zoolflow.transactions.services.webhook import WebhookServiceError
from zoolflow.notifications.models import EmailEvent

# Create your views here.


@api_view(["POST"])
def webhook_reciever(request):
    try:
        payload = request.data["signature"]
        event_data = request.data.get("event-data", {})
        event_id = event_data.get("id", {})
        # check if the recieved webhook has been processed before
        track_duplicate = EmailEvent.objects.filter(event_id=event_id).exists()
        if track_duplicate:
            return Response(
                {"status": "Duplicate event received."},
                status=status.HTTP_200_OK,
            )
        # check webhook signature validity
        verify_mailgun_hmac(payload)
        message_id = (
            request.data.get("event-data", {})
            .get("message", {})
            .get("headers", {})
            .get("message-id")
        )
        # Update the EmailEvent based on the event-data received from webhook
        UpdateEmailEventTracker.with_webhook(event_data, message_id, event_id)
    except WebhookServiceError as e:
        return Response(
            {"status": str(e.message)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response({"status": "received"}, status=status.HTTP_200_OK)
