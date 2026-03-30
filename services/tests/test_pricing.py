"""Unit tests: pricing helpers (no database)."""

import math

from app.pricing import fare_aud, haversine_km, surge_for_prototype


def test_haversine_sydney_short_hop():
    # ~3–5 km in inner Sydney (approximate)
    d = haversine_km(-33.8796, 151.1862, -33.8617, 151.2099)
    assert 2.0 < d < 6.0, d


def test_haversine_identical_zero():
    assert haversine_km(0.0, 0.0, 0.0, 0.0) == 0.0


def test_fare_aud_sedan_no_surge():
    f = fare_aud(10.0, "sedan", surge=1.0)
    # base 3.6 + 10 * 2.85 = 32.1
    assert math.isclose(f, 32.1)


def test_fare_aud_with_surge():
    f = fare_aud(10.0, "sedan", surge=1.08)
    assert f > 32.1


def test_surge_tiers():
    assert surge_for_prototype(5.0) == 1.0
    assert surge_for_prototype(10.0) == 1.08
    assert surge_for_prototype(20.0) == 1.15
