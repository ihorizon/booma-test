import json
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import get_current_user
from app.models import Ride, User
from app.pricing import duration_minutes_stub, fare_aud, haversine_km, surge_for_prototype
from app.schemas import EstimateResponse, RideCreate, RideOut, VehicleOption
from app.stubs.notification_service import NotificationStub

router = APIRouter()
notify = NotificationStub()


def _ride_to_out(r: Ride, include_route: bool) -> RideOut:
    route = json.loads(r.route_json) if r.route_json and include_route else None
    return RideOut(
        id=r.id,
        passenger_id=r.passenger_id,
        driver_id=r.driver_id,
        status=r.status,
        vehicle_type=r.vehicle_type,
        pickup_address=r.pickup_address,
        pickup_lat=r.pickup_lat,
        pickup_lng=r.pickup_lng,
        destination_address=r.destination_address,
        destination_lat=r.destination_lat,
        destination_lng=r.destination_lng,
        fare_estimate=r.fare_estimate,
        fare_final=r.fare_final,
        distance_km=r.distance_km,
        duration_min=r.duration_min,
        surge_multiplier=r.surge_multiplier,
        requested_at=r.requested_at,
        accepted_at=r.accepted_at,
        driver_arrived_at=r.driver_arrived_at,
        started_at=r.started_at,
        completed_at=r.completed_at,
        cancellation_reason=r.cancellation_reason,
        route=route,
    )


@router.get("/estimate", response_model=EstimateResponse)
def estimate(
    _: Annotated[User, Depends(get_current_user)],
    pickup_lat: float = Query(...),
    pickup_lng: float = Query(...),
    destination_lat: float = Query(...),
    destination_lng: float = Query(...),
    vehicle_type: str = Query("sedan"),
):
    dist = haversine_km(pickup_lat, pickup_lng, destination_lat, destination_lng)
    dur = duration_minutes_stub(dist)
    surge = surge_for_prototype(dist)
    types = [
        ("sedan", "Booma Standard"),
        ("suv", "Booma XL"),
        ("minivan", "Booma Group"),
    ]
    vehicles = [
        VehicleOption(
            vehicle_type=vt,
            label=label,
            eta_min=max(3, dur // 3),
            fare_estimate_aud=fare_aud(dist, vt, surge),
        )
        for vt, label in types
    ]
    return EstimateResponse(
        distance_km=round(dist, 2),
        duration_min=dur,
        surge_multiplier=surge,
        vehicles=vehicles,
        requested_vehicle_type=vehicle_type,
    )


@router.get("", response_model=list[RideOut])
def list_rides(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_session)],
):
    if user.role != "passenger":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Passenger rides only in prototype")
    rows = db.scalars(
        select(Ride).where(Ride.passenger_id == user.id).order_by(Ride.requested_at.desc())
    ).all()
    return [_ride_to_out(r, include_route=False) for r in rows]


@router.get("/{ride_id}", response_model=RideOut)
def get_ride(
    ride_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_session)],
):
    ride = db.get(Ride, ride_id)
    if ride is None or ride.passenger_id != user.id:
        raise HTTPException(status_code=404, detail="Ride not found")
    return _ride_to_out(ride, include_route=True)


@router.post("", response_model=RideOut, status_code=status.HTTP_201_CREATED)
def create_ride(
    body: RideCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_session)],
):
    if user.role != "passenger":
        raise HTTPException(status_code=403, detail="Only passengers can book in prototype")
    dist = haversine_km(body.pickup_lat, body.pickup_lng, body.destination_lat, body.destination_lng)
    dur = duration_minutes_stub(dist)
    surge = surge_for_prototype(dist)
    fare = fare_aud(dist, body.vehicle_type, surge)
    rid = f"ride_{uuid.uuid4().hex[:20]}"
    now = datetime.now(timezone.utc)
    route_stub = {
        "polyline_encoded": None,
        "waypoints": [
            {"lat": body.pickup_lat, "lng": body.pickup_lng, "label": body.pickup_address[:80]},
            {"lat": body.destination_lat, "lng": body.destination_lng, "label": body.destination_address[:80]},
        ],
        "bounds": {
            "northeast": {"lat": max(body.pickup_lat, body.destination_lat), "lng": max(body.pickup_lng, body.destination_lng)},
            "southwest": {"lat": min(body.pickup_lat, body.destination_lat), "lng": min(body.pickup_lng, body.destination_lng)},
        },
    }
    ride = Ride(
        id=rid,
        passenger_id=user.id,
        driver_id=None,
        status="SEARCHING",
        vehicle_type=body.vehicle_type,
        pickup_address=body.pickup_address,
        pickup_lat=body.pickup_lat,
        pickup_lng=body.pickup_lng,
        destination_address=body.destination_address,
        destination_lat=body.destination_lat,
        destination_lng=body.destination_lng,
        fare_estimate=fare,
        fare_final=None,
        distance_km=round(dist, 2),
        duration_min=dur,
        surge_multiplier=surge,
        requested_at=now,
        route_json=json.dumps(route_stub),
    )
    db.add(ride)
    db.commit()
    db.refresh(ride)
    notify.send_ride_update(user.id, f"Ride {rid} created (SEARCHING) — matching is stubbed.")
    return _ride_to_out(ride, include_route=True)
