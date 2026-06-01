from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserResponse,
    ChangePasswordRequest, ProfileUpdateRequest,
)
from app.utils.security import verify_password, create_access_token, get_password_hash
from app.utils.deps import get_current_user

router = APIRouter()

ROLE_LABELS = {
    "admin": "Администратор",
    "manager": "Менеджер",
    "warehouse_staff": "Складской сотрудник",
    "director": "Руководитель",
}


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        last_name=user.last_name,
        first_name=user.first_name,
        patronymic=user.patronymic,
        phone=user.phone,
        role=user.role.name,
        role_label=ROLE_LABELS.get(user.role.name, user.role.name),
        is_active=user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учётная запись заблокирована",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.name})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return _to_response(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return _to_response(current_user)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")
    if len(data.new_password) < 4:
        raise HTTPException(status_code=400, detail="Новый пароль слишком короткий (мин. 4 символа)")

    current_user.hashed_password = get_password_hash(data.new_password)
    await db.commit()
    return {"message": "Пароль успешно изменён"}
