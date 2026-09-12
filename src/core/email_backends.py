"""Send mail through Resend's HTTP API instead of SMTP.

Why this exists: DigitalOcean blocks outbound SMTP (ports 25, 465 and 587) by
default on new accounts, as an anti-spam measure. On the Droplet every
connection to smtp.resend.com times out, while https://api.resend.com answers
in 7ms. Render did not block those ports, which is why the contact form worked
there and stopped working here.

Asking DigitalOcean to lift the block is a support ticket with an uncertain
answer and an uncertain date. This route does not depend on anyone's goodwill,
is faster, and gives a readable error instead of a timeout when something is
wrong with the sender or the recipient.

Uses only the standard library, so it adds no dependency.

Configure with:

    EMAIL_BACKEND=core.email_backends.ResendAPIBackend
    RESEND_API_KEY=re_...        # falls back to EMAIL_HOST_PASSWORD

The API key is the same string Resend gives you as the SMTP password.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

API_URL = "https://api.resend.com/emails"
TIMEOUT = 15


class ResendAPIBackend(BaseEmailBackend):
    """Django email backend that posts to the Resend REST API."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = (
            getattr(settings, "RESEND_API_KEY", None)
            or getattr(settings, "EMAIL_HOST_PASSWORD", None)
        )

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            logger.error("RESEND_API_KEY is not set; cannot send mail.")
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY is not set")
            return 0

        sent = 0
        for message in email_messages:
            if self._send(message):
                sent += 1
        return sent

    @staticmethod
    def _payload(message):
        payload = {
            "from": message.from_email,
            "to": list(message.to),
            "subject": message.subject,
        }
        if message.cc:
            payload["cc"] = list(message.cc)
        if message.bcc:
            payload["bcc"] = list(message.bcc)
        if message.reply_to:
            payload["reply_to"] = list(message.reply_to)

        body = message.body or ""
        if getattr(message, "content_subtype", "plain") == "html":
            payload["html"] = body
        else:
            payload["text"] = body

        # EmailMultiAlternatives carries the HTML part alongside the text one.
        for content, mimetype in getattr(message, "alternatives", []) or []:
            if mimetype == "text/html":
                payload["html"] = content

        return payload

    def _send(self, message):
        if not message.to:
            return False

        request = urllib.request.Request(
            API_URL,
            data=json.dumps(self._payload(message)).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8") or "{}")
            logger.info("Resend accepted the message, id=%s", result.get("id"))
            return True

        except urllib.error.HTTPError as exc:
            # Resend explains refusals in the body: an unverified sender domain,
            # a recipient not allowed in testing mode, a bad key. Surface that
            # rather than a bare status code.
            try:
                detail = exc.read().decode("utf-8", "replace")
            except Exception:
                detail = ""
            logger.error("Resend rejected the message: HTTP %s %s",
                         exc.code, detail)
            if not self.fail_silently:
                raise RuntimeError(f"Resend HTTP {exc.code}: {detail}") from exc
            return False

        except Exception as exc:
            logger.error("Could not reach the Resend API: %s: %s",
                         type(exc).__name__, exc)
            if not self.fail_silently:
                raise
            return False
