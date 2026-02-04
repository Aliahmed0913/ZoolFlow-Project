import json
import logging
import requests
from django.conf import settings
from requests.exceptions import HTTPError
from zoolflow.transactions.services.http_client import get_session_with_retries

logger = logging.getLogger(__name__)


class MailGunProviderError(HTTPError):
    # Raised when MailGun API fail or return invalid value
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class MailGunProvider:
    def __init__(self):
        self.api_key = getattr(settings, "MAILGUN_API_KEY")
        self.base_url = getattr(settings, "MAILGUN_BASE_URL")
        self.mailgun_domain = getattr(settings, "EMAIL_DOMAIN")
        self.session = get_session_with_retries()

    def send_email(self, recipient, email_subject, email_body):
        """
        Send email using MailGun API
        """
        endpoint = f"{self.base_url}/v3/{self.mailgun_domain}/messages"
        auth = ("api", self.api_key)
        data = {
            "from": f"Zool_Flow <zoolflow@{self.mailgun_domain}>",
            "to": recipient,
            "subject": email_subject,
            "text": email_body,
        }
        # call MailGun API to send email
        try:
            response = self.session.post(
                url=endpoint, auth=auth, data=data, timeout=(5, 5)
            )
            response.raise_for_status()
            if response.status_code and response.status_code != 200:
                logger.error(
                    f"""
                    Failed to connect to email provider for {recipient}.
                    Status code: {response.status_code}
                    """
                )
                raise MailGunProviderError(
                    "Email provider connection failed",
                    details=f"Status code: {response.status_code}",
                )
            logger.info(f"Mailgun successfully queued '{recipient}' message.")
            result = json.loads(response.text.strip())
            return result

        except requests.RequestException as e:
            logger.error(
                f"""
                Error while sending email to {recipient}: {str(e)}
                """
            )
            raise MailGunProviderError(
                details="Error occurred during email sending", message=str(e)
            )
