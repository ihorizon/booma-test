from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserPublic(BaseModel):
    id: str
    email: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: str
    password: str


class SavedAddressOut(BaseModel):
    id: str
    label: str
    formatted_address: str
    lat: float
    lng: float

    model_config = {"from_attributes": True}


class EstimateQuery(BaseModel):
    pickup_lat: float
    pickup_lng: float
    destination_lat: float
    destination_lng: float
    vehicle_type: str = "sedan"


class VehicleOption(BaseModel):
    vehicle_type: str
    label: str
    eta_min: int
    fare_estimate_aud: float


class EstimateResponse(BaseModel):
    distance_km: float
    duration_min: int
    surge_multiplier: float
    vehicles: list[VehicleOption]
    requested_vehicle_type: str = "sedan"
    stub_note: str = "Pricing from local prototype formula; maps/routing are stubbed."


class RideCreate(BaseModel):
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    destination_address: str
    destination_lat: float
    destination_lng: float
    vehicle_type: str = "sedan"


class RideOut(BaseModel):
    id: str
    passenger_id: str
    driver_id: str | None
    status: str
    vehicle_type: str
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    destination_address: str
    destination_lat: float
    destination_lng: float
    fare_estimate: float | None
    fare_final: float | None
    distance_km: float | None
    duration_min: int | None
    surge_multiplier: float | None
    requested_at: datetime | None
    accepted_at: datetime | None
    driver_arrived_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    cancellation_reason: str | None
    route: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class MapSuggestion(BaseModel):
    id: str
    label: str
    lat: float
    lng: float


class StubPaymentIntent(BaseModel):
    client_secret: str
    payment_intent_id: str
    stub_note: str


class StubNotificationResult(BaseModel):
    queued: bool
    channel: str
    stub_payload_preview: str
