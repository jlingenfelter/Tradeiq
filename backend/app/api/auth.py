from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    user = create_user(db, body.email, body.password)
    _, token = authenticate_user(db, body.email, body.password)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=str(user.id), email=user.email, created_at=user.created_at),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user, token = authenticate_user(db, body.email, body.password)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=str(user.id), email=user.email, created_at=user.created_at),
    )


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=str(current_user.id), email=current_user.email, created_at=current_user.created_at)
