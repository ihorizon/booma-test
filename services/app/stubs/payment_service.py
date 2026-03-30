"""Stubbed Stripe — logs and returns fake ids (no network)."""

import logging
import uuid

from app.schemas import StubPaymentIntent

log = logging.getLogger(__name__)


class PaymentStub:
    def create_setup_intent(self, user_id: str) -> StubPaymentIntent:
        pi = f"pi_stub_{uuid.uuid4().hex[:12]}"
        secret = f"{pi}_secret_stub"
        log.info("stub.payment setup_intent user=%s payment_intent=%s", user_id, pi)
        return StubPaymentIntent(
            client_secret=secret,
            payment_intent_id=pi,
            stub_note="No call to Stripe; safe for local prototype.",
        )

    def capture_ride_payment(
        self,
        ride_id: str,
        amount_aud: float,
        idempotency_key: str,
    ) -> dict:
        log.info(
            "stub.payment capture ride=%s amount=%s idempotency=%s",
            ride_id,
            amount_aud,
            idempotency_key,
        )
        return {
            "status": "succeeded",
            "payment_intent_id": f"pi_stub_{uuid.uuid4().hex[:10]}",
            "amount": amount_aud,
        }
