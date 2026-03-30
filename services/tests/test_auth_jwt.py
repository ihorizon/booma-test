"""JWT behaviour aligned with TEST_PLAN §2."""

import time
from unittest.mock import MagicMock

from fastapi import HTTPException
from jose import jwt

from app.config import settings
from app.deps import get_current_user


def _bearer(token: str):
    class C:
        scheme = "Bearer"
        credentials = token

    return C()


def test_jwt_payload_contains_sub_role_exp():
    from app.routers.auth import _create_access_token

    token, secs = _create_access_token("usr_test", "passenger")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "usr_test"
    assert payload["role"] == "passenger"
    assert "exp" in payload and payload["exp"] > int(time.time())
    assert secs > 0


def test_expired_token_rejected():
    past = int(time.time()) - 60
    token = jwt.encode(
        {"sub": "usr_x", "role": "passenger", "exp": past},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    db = MagicMock()
    try:
        get_current_user(db=db, cred=_bearer(token))
    except HTTPException as e:
        assert e.status_code == 401
    else:
        raise AssertionError("expected 401")
