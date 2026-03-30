from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    saved_addresses: Mapped[list["SavedAddress"]] = relationship(back_populates="user")
    rides_as_passenger: Mapped[list["Ride"]] = relationship(
        back_populates="passenger",
        foreign_keys="Ride.passenger_id",
    )


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    vehicle_make: Mapped[str] = mapped_column(String(64))
    vehicle_model: Mapped[str] = mapped_column(String(64))
    vehicle_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vehicle_colour: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_plate: Mapped[str] = mapped_column(String(32))
    vehicle_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    current_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_trips: Mapped[int | None] = mapped_column(Integer, nullable=True)
    licence_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    licence_expiry: Mapped[str | None] = mapped_column(String(32), nullable=True)
    accreditation_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    online_since: Mapped[datetime | None] = mapped_column(nullable=True)


class SavedAddress(Base):
    __tablename__ = "saved_addresses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(64))
    formatted_address: Mapped[str] = mapped_column(String(512))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="saved_addresses")


class Ride(Base):
    __tablename__ = "rides"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    passenger_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    driver_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("drivers.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    vehicle_type: Mapped[str] = mapped_column(String(32))
    pickup_address: Mapped[str] = mapped_column(String(512))
    pickup_lat: Mapped[float] = mapped_column(Float)
    pickup_lng: Mapped[float] = mapped_column(Float)
    destination_address: Mapped[str] = mapped_column(String(512))
    destination_lat: Mapped[float] = mapped_column(Float)
    destination_lng: Mapped[float] = mapped_column(Float)
    fare_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    fare_final: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    surge_multiplier: Mapped[float | None] = mapped_column(Float, nullable=True)
    requested_at: Mapped[datetime | None] = mapped_column(nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    driver_arrived_at: Mapped[datetime | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    passenger_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    driver_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    passenger: Mapped["User"] = relationship(
        back_populates="rides_as_passenger",
        foreign_keys=[passenger_id],
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ride_id: Mapped[str] = mapped_column(String(64), ForeignKey("rides.id"), index=True)
    passenger_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(32))
    card_brand: Mapped[str | None] = mapped_column(String(32), nullable=True)
    card_last4: Mapped[str | None] = mapped_column(String(8), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(nullable=True)
