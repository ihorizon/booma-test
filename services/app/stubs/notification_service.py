"""Stubbed SMS/email — log only."""

import logging

log = logging.getLogger(__name__)


class NotificationStub:
    def send_ride_update(self, user_id: str, message: str) -> None:
        log.info("stub.notification user=%s message=%s", user_id, message)
