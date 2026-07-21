from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import generate_jwt_token, generate_plain_password, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserProfileResponse,
    UserProfileUpdate,
)
from app.services.email_service import send_registration_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    email = payload.email.lower().strip()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с таким email уже существует.")

    plain_password = generate_plain_password()
    user = User(
        email=email,
        password_hash=hash_password(plain_password),
        last_name=None,
        first_name=None,
        middle_name=None,
    )
    db.add(user)
    db.flush()

    try:
        send_registration_password(email_to=email, plain_password=plain_password)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось отправить письмо с паролем: {exc}",
        ) from exc

    db.commit()
    return RegisterResponse(message="Пользователь зарегистрирован. Пароль отправлен на email.")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль.")

    token = generate_jwt_token(user_id=user.id, email=user.email)
    return LoginResponse(access_token=token, is_admin=user.is_admin)


def to_profile_response(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        email=user.email,
        last_name=user.last_name,
        first_name=user.first_name,
        middle_name=user.middle_name,
    )


@router.get("/me", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return to_profile_response(current_user)


@router.patch("/me", response_model=UserProfileResponse)
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    changes = payload.model_dump(exclude_unset=True)
    if "last_name" in changes:
        current_user.last_name = changes["last_name"].strip() if changes["last_name"] else None
    if "first_name" in changes:
        current_user.first_name = changes["first_name"].strip() if changes["first_name"] else None
    if "middle_name" in changes:
        current_user.middle_name = changes["middle_name"].strip() if changes["middle_name"] else None

    db.commit()
    db.refresh(current_user)
    return to_profile_response(current_user)
