from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import generate_jwt_token, generate_plain_password, hash_password, verify_password
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


def register_user(db: Session, payload: RegisterRequest) -> RegisterResponse:
    email = _normalize_email(payload.email)
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


def authenticate_user(db: Session, payload: LoginRequest) -> LoginResponse:
    email = _normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль.")

    token = generate_jwt_token(user_id=user.id, email=user.email)
    return LoginResponse(access_token=token, is_admin=user.is_admin)


def user_profile(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        email=user.email,
        last_name=user.last_name,
        first_name=user.first_name,
        middle_name=user.middle_name,
    )


def update_user_profile(db: Session, user: User, payload: UserProfileUpdate) -> UserProfileResponse:
    changes = payload.model_dump(exclude_unset=True)
    if "last_name" in changes:
        user.last_name = _clean_optional_text(changes["last_name"])
    if "first_name" in changes:
        user.first_name = _clean_optional_text(changes["first_name"])
    if "middle_name" in changes:
        user.middle_name = _clean_optional_text(changes["middle_name"])

    db.commit()
    db.refresh(user)
    return user_profile(user)


def _normalize_email(email: str) -> str:
    return email.lower().strip()


def _clean_optional_text(value: str | None) -> str | None:
    return value.strip() if value else None
