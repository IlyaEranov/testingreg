from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/count")
async def notifications_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(func.count(Notification.id)))
    return {"count": result.scalar() or 0}


@router.get("/return/{return_id}", response_model=list[NotificationResponse])
async def list_for_return(
    return_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.return_request_id == return_id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()
