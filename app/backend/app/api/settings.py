from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.setting import AppSetting
from app.models.user import User
from app.utils.deps import get_current_user, require_roles

router = APIRouter()

# Ключи настроек, доступных через интерфейс
KEYS = [
    "onec_api_url", "onec_api_token",
    "smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from",
    "sms_api_url", "sms_api_key", "sms_sender",
]


class SettingsPayload(BaseModel):
    onec_api_url: str | None = None
    onec_api_token: str | None = None
    smtp_host: str | None = None
    smtp_port: str | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    sms_api_url: str | None = None
    sms_api_key: str | None = None
    sms_sender: str | None = None


async def _get_all(db: AsyncSession) -> dict:
    result = await db.execute(select(AppSetting).where(AppSetting.key.in_(KEYS)))
    data = {s.key: s.value for s in result.scalars().all()}
    return {k: data.get(k, "") for k in KEYS}


@router.get("/")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_all(db)


@router.put("/")
async def update_settings(
    data: SettingsPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    for key, value in data.model_dump(exclude_unset=True).items():
        existing = await db.get(AppSetting, key)
        if existing:
            existing.value = value
        else:
            db.add(AppSetting(key=key, value=value))
    await db.commit()
    return await _get_all(db)
