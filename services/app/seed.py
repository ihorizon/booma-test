import json
import logging
from datetime import datetime
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Driver, Payment, Ride, SavedAddress, User

log = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _parse_dt(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seed_if_empty(session: Session) -> bool:
    n = session.scalar(select(func.count()).select_from(User))
    if n and n > 0:
        log.info("Database already seeded (%s users); skipping.", n)
        return False

    path: Path = settings.synthetic_data_path
    if not path.is_file():
        log.warning("Synthetic data not found at %s — cannot seed.", path)
        return False

    data = json.loads(path.read_text(encoding="utf-8"))
    demo_hash = pwd_context.hash(settings.prototype_password)

    for row in data.get("users", []):
        session.add(
            User(
                id=row["id"],
                email=row["email"],
                phone=row.get("phone"),
                full_name=row["full_name"],
                password_hash=demo_hash,
                role=row["role"],
                created_at=_parse_dt(row.get("created_at")),
                updated_at=_parse_dt(row.get("updated_at")),
            )
        )

    for row in data.get("drivers", []):
        session.add(
            Driver(
                id=row["id"],
                user_id=row["user_id"],
                vehicle_make=row["vehicle_make"],
                vehicle_model=row["vehicle_model"],
                vehicle_year=row.get("vehicle_year"),
                vehicle_colour=row.get("vehicle_colour"),
                vehicle_plate=row["vehicle_plate"],
                vehicle_type=row["vehicle_type"],
                status=row["status"],
                current_lat=row.get("current_lat"),
                current_lng=row.get("current_lng"),
                rating=row.get("rating"),
                total_trips=row.get("total_trips"),
                licence_number=row.get("licence_number"),
                licence_expiry=row.get("licence_expiry"),
                accreditation_number=row.get("accreditation_number"),
                online_since=_parse_dt(row.get("online_since")),
            )
        )

    for row in data.get("saved_addresses", []):
        session.add(
            SavedAddress(
                id=row["id"],
                user_id=row["user_id"],
                label=row["label"],
                formatted_address=row["formatted_address"],
                lat=row["lat"],
                lng=row["lng"],
            )
        )

    for row in data.get("rides", []):
        route = row.get("route")
        route_json = json.dumps(route) if route is not None else None
        session.add(
            Ride(
                id=row["id"],
                passenger_id=row["passenger_id"],
                driver_id=row.get("driver_id"),
                status=row["status"],
                vehicle_type=row["vehicle_type"],
                pickup_address=row["pickup_address"],
                pickup_lat=row["pickup_lat"],
                pickup_lng=row["pickup_lng"],
                destination_address=row["destination_address"],
                destination_lat=row["destination_lat"],
                destination_lng=row["destination_lng"],
                fare_estimate=row.get("fare_estimate"),
                fare_final=row.get("fare_final"),
                distance_km=row.get("distance_km"),
                duration_min=row.get("duration_min"),
                surge_multiplier=row.get("surge_multiplier"),
                requested_at=_parse_dt(row.get("requested_at")),
                accepted_at=_parse_dt(row.get("accepted_at")),
                driver_arrived_at=_parse_dt(row.get("driver_arrived_at")),
                started_at=_parse_dt(row.get("started_at")),
                completed_at=_parse_dt(row.get("completed_at")),
                cancellation_reason=row.get("cancellation_reason"),
                passenger_rating=row.get("passenger_rating"),
                driver_rating=row.get("driver_rating"),
                route_json=route_json,
            )
        )

    for row in data.get("payments", []):
        session.add(
            Payment(
                id=row["id"],
                ride_id=row["ride_id"],
                passenger_id=row["passenger_id"],
                stripe_payment_intent_id=row.get("stripe_payment_intent_id"),
                amount=row["amount"],
                currency=row["currency"],
                status=row["status"],
                card_brand=row.get("card_brand"),
                card_last4=row.get("card_last4"),
                idempotency_key=row.get("idempotency_key"),
                captured_at=_parse_dt(row.get("captured_at")),
            )
        )

    session.commit()
    log.info(
        "Seeded SQLite from synthetic data (password for all users: %s).",
        settings.prototype_password,
    )
    return True
