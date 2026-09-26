"""Outbound email. In this demo, messages go to an in-memory outbox."""
import logging

log = logging.getLogger("payments.notify")
OUTBOX: list[dict] = []


def send_email(to: str, body: str) -> None:
    OUTBOX.append({"to": to, "body": body})
    log.info("email sent to %s", to)
