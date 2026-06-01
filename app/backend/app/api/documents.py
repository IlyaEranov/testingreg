from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ReturnRequest, Document
from app.models.user import User
from app.schemas.return_request import DocumentResponse
from app.services.document_service import generate_and_save_document, DOCUMENT_TYPES
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/types")
async def get_document_types():
    """List available document types."""
    return [{"code": k, "name": v} for k, v in DOCUMENT_TYPES.items()]


@router.get("/{return_id}", response_model=list[DocumentResponse])
async def list_documents(
    return_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .where(Document.return_request_id == return_id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{return_id}/generate")
async def generate_document(
    return_id: int,
    doc_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if doc_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Неизвестный тип документа")

    result = await db.execute(
        select(ReturnRequest)
        .options(
            selectinload(ReturnRequest.client),
            selectinload(ReturnRequest.reason),
            selectinload(ReturnRequest.items),
        )
        .where(ReturnRequest.id == return_id)
    )
    rr = result.scalar_one_or_none()
    if not rr:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    doc = await generate_and_save_document(db, rr, doc_type)
    await db.commit()

    return {
        "id": doc.id,
        "file_name": doc.file_name,
        "document_type": doc.document_type,
        "message": f"Документ «{DOCUMENT_TYPES[doc_type]}» сформирован",
    }


@router.get("/download/{document_id}")
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    return FileResponse(
        path=doc.file_path,
        filename=doc.file_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
