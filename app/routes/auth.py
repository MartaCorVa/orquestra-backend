from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.security import create_access_token, verify_password, hash_password
from app.models.user import User
from app.schemas.auth import LoginResponse, ChangePasswordRequest

router = APIRouter(prefix = "/auth", tags = ["Auth"])


@router.post("/login", response_model = LoginResponse)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid credentials"
        )

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "must_change_password": user.must_change_password,
        "user": user.email
    }


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not verify_password(payload.current_password, current_user.password):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Current password is incorrect"
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "New password must be different from the current password"
        )

    current_user.password = hash_password(payload.new_password)
    current_user.must_change_password = False

    db.commit()
    db.refresh(current_user)

    return {"message": "Password updated successfully"}