from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ReturnRequest
from app.models.user import User
from app.schemas.return_request import WarehouseCheckCreate, ReturnRequestListResponse
from app.services.return_service import submit_warehouse_check
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/pending", response_model=list[ReturnRequestListResponse])
async def get_pending_checks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get returns waiting for warehouse check."""
    result = await db.execute(
        select(ReturnRequest)
        .options(
            selectinload(ReturnRequest.client),
            selectinload(ReturnRequest.reason),
            selectinload(ReturnRequest.manager),
            selectinload(ReturnRequest.warehouse),
        )
        .where(ReturnRequest.status == "warehouse")
        .order_by(ReturnRequest.created_at.asc())
    )
    returns = result.scalars().all()

    return [
        ReturnRequestListResponse(
            id=r.id,
            number=r.number,
            client_name=r.client.name if r.client else "",
            return_type=r.return_type,
            reason_name=r.reason.name if r.reason else None,
            status=r.status,
            manager_name=r.manager.full_name if r.manager else None,
            warehouse_name=r.warehouse.name if r.warehouse else None,
            total_amount=r.total_amount,
            created_at=r.created_at,
        )
        for r in returns
    ]


@router.post("/{return_id}/check")
async def submit_check(
    return_id: int,
    checks: list[WarehouseCheckCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        rr = await submit_warehouse_check(db, return_id, checks, current_user)
        return {"id": rr.id, "status": rr.status, "message": "Проверка сохранена"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{return_id}/photos")
async def upload_photos(
    return_id: int,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload inspection photos (saves to uploads dir)."""
    import os
    from app.config import settings

    upload_dir = os.path.join(settings.UPLOAD_DIR, str(return_id))
    os.makedirs(upload_dir, exist_ok=True)

    saved = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved.append({"filename": file.filename, "path": file_path})

    return {"uploaded": len(saved), "files": saved}
