from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.deps import get_current_user
from app.models import User
from app.stubs.maps_service import MapsStub
from app.stubs.payment_service import PaymentStub

router = APIRouter()
_maps = MapsStub()
_payments = PaymentStub()


@router.get("/maps/autocomplete")
def maps_autocomplete(
    _: Annotated[User, Depends(get_current_user)],
    q: str = Query("", alias="q"),
    limit: int = Query(8, ge=1, le=20),
):
    return _maps.autocomplete(q, limit=limit)


@router.post("/payments/setup-intent")
def payment_setup_intent(user: Annotated[User, Depends(get_current_user)]):
    return _payments.create_setup_intent(user.id)
