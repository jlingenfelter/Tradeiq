from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse, UserUpdateRequest
from app.services.auth_service import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id), email=user.email,
        base_currency=user.base_currency, timezone=user.timezone,
        created_at=user.created_at,
    )


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    user = create_user(db, body.email, body.password, body.base_currency, body.timezone)
    _, token = authenticate_user(db, body.email, body.password)
    return TokenResponse(access_token=token, user=_user_response(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user, token = authenticate_user(db, body.email, body.password)
    return TokenResponse(access_token=token, user=_user_response(user))


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return _user_response(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.base_currency is not None:
        current_user.base_currency = body.base_currency
    if body.timezone is not None:
        current_user.timezone = body.timezone
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)
