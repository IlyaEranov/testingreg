from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ReturnRequest, Client
from app.models.user import User
from app.schemas.return_request import (
    ReturnRequestCreate, ReturnRequestListResponse,
    ReturnRequestDetailResponse, StatusTransition,
    ExaminationCreate, ExaminationResultUpdate,
)
from app.services.return_service import (
    create_return_request, transition_status, get_return_detail,
    send_claim_to_factory, submit_factory_result,
)
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=list[ReturnRequestListResponse])
async def list_returns(
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    client: str | None = None,
    scope: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(ReturnRequest)
        .options(
            selectinload(ReturnRequest.client),
            selectinload(ReturnRequest.reason),
            selectinload(ReturnRequest.manager),
            selectinload(ReturnRequest.warehouse),
        )
    )

    # Ограничение видимости по роли:
    #  - менеджер: по умолчанию свои заявки (scope=all — все);
    #  - сотрудник претензионного отдела: заявки на стадиях претензии и приёмки;
    #  - логистика: заявки, переданные в перевозку;
    #  - руководитель/админ: все заявки.
    role = current_user.role.name if current_user.role else ""
    claims_stages = ["client_data", "claim_factory", "factory_review",
                     "factory_done", "in_transit", "received"]
    if role == "manager" and scope != "all":
        query = query.where(ReturnRequest.manager_id == current_user.id)
    elif role == "claims":
        query = query.where(ReturnRequest.status.in_(claims_stages))
    elif role == "logistics":
        query = query.where(ReturnRequest.status == "in_transit")

    if status:
        query = query.where(ReturnRequest.status == status)
    if date_from:
        query = query.where(ReturnRequest.created_at >= date_from)
    if date_to:
        query = query.where(ReturnRequest.created_at <= date_to + "T23:59:59")
    if client:
        query = query.where(
            ReturnRequest.client.has(
                func.lower(Client.name).contains(client.lower())
            )
        )

    query = query.order_by(ReturnRequest.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
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


@router.post("/", response_model=ReturnRequestListResponse, status_code=201)
async def create_return(
    data: ReturnRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rr = await create_return_request(db, data, current_user)

    # Reload with relationships
    result = await db.execute(
        select(ReturnRequest)
        .options(
            selectinload(ReturnRequest.client),
            selectinload(ReturnRequest.reason),
            selectinload(ReturnRequest.manager),
            selectinload(ReturnRequest.warehouse),
            selectinload(ReturnRequest.items),
        )
        .where(ReturnRequest.id == rr.id)
    )
    rr = result.scalar_one()

    # Документы при создании не формируются: заявка регистрируется в статусе
    # «Создана», далее по ходу процесса формируются претензия, маршрутный лист и акты.

    return ReturnRequestListResponse(
        id=rr.id,
        number=rr.number,
        client_name=rr.client.name if rr.client else "",
        return_type=rr.return_type,
        reason_name=rr.reason.name if rr.reason else None,
        status=rr.status,
        manager_name=rr.manager.full_name if rr.manager else None,
        warehouse_name=rr.warehouse.name if rr.warehouse else None,
        total_amount=rr.total_amount,
        created_at=rr.created_at,
    )


@router.get("/{return_id}", response_model=ReturnRequestDetailResponse)
async def get_return(
    return_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    detail = await get_return_detail(db, return_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return detail


@router.post("/{return_id}/status")
async def change_status(
    return_id: int,
    data: StatusTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        rr = await transition_status(
            db, return_id, data.new_status, current_user, data.comment, data.outcome
        )
        return {"id": rr.id, "status": rr.status, "message": "Статус обновлён"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{return_id}/claim")
async def send_claim(
    return_id: int,
    data: ExaminationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сформировать и направить претензию заводу-изготовителю."""
    try:
        claim = await send_claim_to_factory(
            db, return_id, data.supplier_id, current_user, data.details
        )
        return {"id": claim.id, "message": "Претензия направлена заводу"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{return_id}/claim/result")
async def submit_claim_result(
    return_id: int,
    data: ExaminationResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Внести заключение завода по претензии."""
    try:
        rr = await submit_factory_result(
            db, return_id, data.conclusion, data.details, current_user
        )
        return {"id": rr.id, "status": rr.status, "message": "Заключение завода сохранено"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
