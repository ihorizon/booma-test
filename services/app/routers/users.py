from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.deps import get_current_user
from app.models import SavedAddress, User
from app.schemas import SavedAddressOut, UserPublic

router = APIRouter()


@router.get("/me", response_model=UserPublic)
def read_me(user: Annotated[User, Depends(get_current_user)]):
    return UserPublic.model_validate(user)


@router.get("/saved-addresses", response_model=list[SavedAddressOut])
def saved_addresses(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_session)],
):
    rows = db.scalars(select(SavedAddress).where(SavedAddress.user_id == user.id)).all()
    return [SavedAddressOut.model_validate(r) for r in rows]
