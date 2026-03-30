from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session
from app.models import User
from app.schemas import LoginRequest, TokenResponse

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_access_token(user_id: str, role: str) -> tuple[str, int]:
    expire_delta = timedelta(minutes=settings.access_token_expire_minutes)
    now = datetime.now(timezone.utc)
    exp = now + expire_delta
    payload = {
        "sub": user_id,
        "role": role,
        "exp": int(exp.timestamp()),
        "iat": int(now.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, int(expire_delta.total_seconds())


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_session)):
    email = body.email.strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token, secs = _create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, expires_in=secs)
