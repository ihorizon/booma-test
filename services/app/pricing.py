import math
from typing import Literal

VehicleType = Literal["sedan", "suv", "minivan"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def duration_minutes_stub(distance_km: float) -> int:
    return max(5, int(distance_km * 2.8 + 3))


_PER_KM: dict[str, float] = {"sedan": 2.85, "suv": 3.15, "minivan": 3.45}


def fare_aud(distance_km: float, vehicle_type: str, surge: float = 1.0) -> float:
    base = 3.6
    rate = _PER_KM.get(vehicle_type, _PER_KM["sedan"])
    raw = (base + distance_km * rate) * surge
    return round(raw, 2)


def surge_for_prototype(distance_km: float) -> float:
    """Deterministic pseudo-surge for demo (not real demand)."""
    if distance_km > 15:
        return 1.15
    if distance_km > 8:
        return 1.08
    return 1.0
