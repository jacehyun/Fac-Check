from base64 import urlsafe_b64decode
from email.parser import BytesParser
from email.policy import default
from unittest.mock import patch

from django.core.mail import EmailMessage, get_connection, send_mail
from django.test import SimpleTestCase, override_settings
from google.auth.exceptions import RefreshError
from requests import Response

from accounts.email_backends import GMAIL_SEND_SCOPE, GMAIL_SEND_URL


@override_settings(
    EMAIL_BACKEND="accounts.email_backends.GmailAPIBackend",
    EMAIL_TIMEOUT=10,
    GMAIL_CLIENT_ID="test-client",
    GMAIL_CLIENT_SECRET="test-secret",
    GMAIL_REFRESH_TOKEN="test-refresh-token",
)
class GmailAPIBackendTests(SimpleTestCase):
    @patch("accounts.email_backends.AuthorizedSession")
    def test_sends_existing_django_message_as_mime(self, session_factory):
        session = session_factory.return_value.__enter__.return_value
        message = EmailMessage(
            "Your Fac-Check Login Code",
            "Example code.",
            "Fac-Check <sender@example.com>",
            ["recipient@example.com"],
            bcc=["blind@example.com"],
            reply_to=["reply@example.com"],
        )

        self.assertEqual(message.send(), 1)
        credentials = session_factory.call_args.args[0]
        self.assertEqual(credentials.scopes, [GMAIL_SEND_SCOPE])
        self.assertEqual(session.post.call_args.args, (GMAIL_SEND_URL,))
        self.assertEqual(session.post.call_args.kwargs["timeout"], 10)
        payload = urlsafe_b64decode(session.post.call_args.kwargs["json"]["raw"])
        mime = BytesParser(policy=default).parsebytes(payload)
        self.assertEqual(mime["To"], "recipient@example.com")
        self.assertEqual(mime["Bcc"], "blind@example.com")
        self.assertEqual(mime["Reply-To"], "reply@example.com")
        self.assertEqual(mime["From"], "Fac-Check <sender@example.com>")
        self.assertEqual(mime.get_content().strip(), "Example code.")

    @patch("accounts.email_backends.AuthorizedSession")
    def test_oauth_failure_is_handled_by_existing_views(self, session_factory):
        session = session_factory.return_value.__enter__.return_value
        session.post.side_effect = RefreshError("private provider response")

        with self.assertLogs("accounts.email_backends", level="WARNING") as logs:
            with self.assertRaisesRegex(OSError, "Gmail API could not send"):
                send_mail("Subject", "Body", "sender@example.com", ["recipient@example.com"])
        self.assertIn("error=RefreshError", logs.output[0])
        self.assertNotIn("private provider response", logs.output[0])

    @patch("accounts.email_backends.AuthorizedSession")
    def test_fail_silently_reports_only_successful_messages(self, session_factory):
        session = session_factory.return_value.__enter__.return_value
        failed = Response()
        failed.status_code = 403
        accepted = Response()
        accepted.status_code = 200
        session.post.side_effect = [failed, accepted]
        message = EmailMessage("Subject", "Body", "sender@example.com", ["recipient@example.com"])
        no_recipients = EmailMessage("Subject", "Body", "sender@example.com")

        connection = get_connection(fail_silently=True)
        with self.assertLogs("accounts.email_backends", level="WARNING") as logs:
            self.assertEqual(connection.send_messages([no_recipients, message, message]), 1)
        self.assertEqual(session.post.call_count, 2)
        self.assertIn("http_status=403", logs.output[0])
