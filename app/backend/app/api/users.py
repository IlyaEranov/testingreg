from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, Role
from app.schemas.directory import UserCreate, UserUpdate, UserListResponse
from app.utils.security import get_password_hash
from app.utils.deps import get_current_user, require_roles

router = APIRouter()


@router.get("/", response_model=list[UserListResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User).options(selectinload(User.role)).order_by(User.id)
    )
    users = result.scalars().all()
    return [
        UserListResponse(
            id=u.id, email=u.email,
            last_name=u.last_name, first_name=u.first_name,
            patronymic=u.patronymic, phone=u.phone,
            role_name=u.role.name if u.role else None,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.post("/", response_model=UserListResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "director")),
):
    # Check email unique
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже используется")

    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        last_name=data.last_name,
        first_name=data.first_name,
        patronymic=data.patronymic,
        phone=data.phone,
        role_id=data.role_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user.id)
    )
    user = result.scalar_one()

    return UserListResponse(
        id=user.id, email=user.email,
        last_name=user.last_name, first_name=user.first_name,
        patronymic=user.patronymic, phone=user.phone,
        role_name=user.role.name if user.role else None,
        is_active=user.is_active,
    )


@router.put("/{user_id}", response_model=UserListResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "director")),
):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return UserListResponse(
        id=user.id, email=user.email,
        last_name=user.last_name, first_name=user.first_name,
        patronymic=user.patronymic, phone=user.phone,
        role_name=user.role.name if user.role else None,
        is_active=user.is_active,
    )


@router.get("/roles")
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).order_by(Role.id))
    roles = result.scalars().all()
    return [{"id": r.id, "name": r.name, "description": r.description} for r in roles]
