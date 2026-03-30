from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session
from app.models import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_session)],
    cred: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if cred is None or cred.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(cred.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None

    user = db.get(User, sub)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
