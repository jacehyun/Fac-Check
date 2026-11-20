"""Send Django email messages through the Gmail API."""

import logging
from base64 import urlsafe_b64encode
from email.policy import SMTP

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from requests import RequestException

logger = logging.getLogger(__name__)

GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GmailAPIBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        credentials = Credentials(
            token=None,
            token_uri=GOOGLE_TOKEN_URL,
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            refresh_token=settings.GMAIL_REFRESH_TOKEN,
            scopes=[GMAIL_SEND_SCOPE],
        )
        sent = 0
        with AuthorizedSession(credentials, refresh_timeout=settings.EMAIL_TIMEOUT) as session:
            for email_message in email_messages:
                if not email_message.recipients():
                    continue

                message = email_message.message(policy=SMTP)
                # Gmail uses the MIME headers for routing, including blind copies.
                del message["Bcc"]
                if email_message.bcc:
                    message["Bcc"] = ", ".join(email_message.bcc)
                raw = urlsafe_b64encode(message.as_bytes()).decode("ascii")

                try:
                    response = session.post(
                        GMAIL_SEND_URL,
                        json={"raw": raw},
                        timeout=settings.EMAIL_TIMEOUT,
                    )
                    response.raise_for_status()
                except (GoogleAuthError, RequestException) as exc:
                    logger.warning(
                        "Gmail API send failed (error=%s, http_status=%s)",
                        type(exc).__name__,
                        getattr(getattr(exc, "response", None), "status_code", None),
                    )
                    if not self.fail_silently:
                        # Existing OTP and contact views handle email delivery OSErrors.
                        raise OSError("Gmail API could not send the message.") from None
                else:
                    sent += 1
        return sent
