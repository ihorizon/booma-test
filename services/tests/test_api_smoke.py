"""API smoke tests — TEST_PLAN §1. Use `with TestClient(app)` so lifespan + seed run."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

PASSENGER_EMAIL = "sophie.zhang@gmail.com"
PASSENGER_PASSWORD = "demo"
SOPHIE_USER_ID = "usr_01HGKX2M3N4P5Q6R7S8T9UAB"
# Liam's ride (different passenger) — synthetic-data.json
OTHER_PASSENGER_RIDE_ID = "ride_01HGKX3A1B2C3D4E5F6G7H9J"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("storage") == "sqlite"


def test_login_ok(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": PASSENGER_EMAIL, "password": PASSENGER_PASSWORD},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body.get("token_type") == "bearer"
    assert body.get("expires_in", 0) > 0


def test_login_bad_password(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": PASSENGER_EMAIL, "password": "wrong"},
    )
    assert r.status_code == 401


def _auth_headers(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": PASSENGER_EMAIL, "password": PASSENGER_PASSWORD},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_users_me(client):
    r = client.get("/api/v1/users/me", headers=_auth_headers(client))
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == PASSENGER_EMAIL
    assert data["role"] == "passenger"


def test_saved_addresses_scoped(client):
    r = client.get("/api/v1/users/saved-addresses", headers=_auth_headers(client))
    assert r.status_code == 200
    addrs = r.json()
    assert len(addrs) >= 1
    assert all(a["id"] for a in addrs)
    assert all("formatted_address" in a for a in addrs)


def test_list_bookings_passenger(client):
    r = client.get("/api/v1/bookings", headers=_auth_headers(client))
    assert r.status_code == 200
    rides = r.json()
    assert isinstance(rides, list)
    assert len(rides) >= 1
    assert all(ride["passenger_id"] == SOPHIE_USER_ID for ride in rides)


def test_estimate(client):
    h = _auth_headers(client)
    r = client.get(
        "/api/v1/bookings/estimate",
        params={
            "pickup_lat": -33.87,
            "pickup_lng": 151.2,
            "destination_lat": -33.9,
            "destination_lng": 151.17,
            "vehicle_type": "suv",
        },
        headers=h,
    )
    assert r.status_code == 200
    data = r.json()
    assert "vehicles" in data and len(data["vehicles"]) == 3
    assert data.get("distance_km", 0) > 0
    assert "stub_note" in data
    assert data.get("requested_vehicle_type") == "suv"


def test_create_booking(client):
    h = _auth_headers(client)
    r = client.post(
        "/api/v1/bookings",
        headers=h,
        json={
            "pickup_address": "1 Test St",
            "pickup_lat": -33.88,
            "pickup_lng": 151.19,
            "destination_address": "2 Demo Ave",
            "destination_lat": -33.89,
            "destination_lng": 151.18,
            "vehicle_type": "sedan",
        },
    )
    assert r.status_code == 201
    assert r.json().get("status") == "SEARCHING"


def test_stub_maps_autocomplete(client):
    r = client.get(
        "/api/v1/stub/maps/autocomplete",
        params={"q": "sydney"},
        headers=_auth_headers(client),
    )
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_stub_payment_setup_intent(client):
    r = client.post(
        "/api/v1/stub/payments/setup-intent",
        headers=_auth_headers(client),
    )
    assert r.status_code == 200
    body = r.json()
    assert "payment_intent_id" in body
    assert "client_secret" in body


def test_booking_idor_other_users_ride(client):
    h = _auth_headers(client)
    r = client.get(f"/api/v1/bookings/{OTHER_PASSENGER_RIDE_ID}", headers=h)
    assert r.status_code == 404
