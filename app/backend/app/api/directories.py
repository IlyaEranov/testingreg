from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.directory import ReturnReason, ReturnStatus, Supplier, Warehouse
from app.models.user import User
from app.schemas.directory import (
    ReasonResponse, ReasonCreate,
    SupplierResponse, SupplierCreate,
    WarehouseResponse, WarehouseCreate,
)
from app.utils.deps import get_current_user

router = APIRouter()


# ===== Reasons =====
@router.get("/reasons", response_model=list[ReasonResponse])
async def list_reasons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReturnReason).order_by(ReturnReason.id))
    return result.scalars().all()


@router.post("/reasons", response_model=ReasonResponse, status_code=201)
async def create_reason(
    data: ReasonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reason = ReturnReason(**data.model_dump())
    db.add(reason)
    await db.commit()
    await db.refresh(reason)
    return reason


@router.put("/reasons/{reason_id}", response_model=ReasonResponse)
async def update_reason(
    reason_id: int,
    data: ReasonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ReturnReason).where(ReturnReason.id == reason_id))
    reason = result.scalar_one_or_none()
    if not reason:
        raise HTTPException(status_code=404, detail="Причина не найдена")
    for field, value in data.model_dump().items():
        setattr(reason, field, value)
    await db.commit()
    await db.refresh(reason)
    return reason


# ===== Statuses =====
@router.get("/statuses")
async def list_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReturnStatus).order_by(ReturnStatus.sort_order))
    statuses = result.scalars().all()
    return [
        {"id": s.id, "name": s.name, "code": s.code, "description": s.description}
        for s in statuses
    ]


# ===== Suppliers =====
@router.get("/suppliers", response_model=list[SupplierResponse])
async def list_suppliers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).order_by(Supplier.id))
    return result.scalars().all()


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    for field, value in data.model_dump().items():
        setattr(supplier, field, value)
    await db.commit()
    await db.refresh(supplier)
    return supplier


# ===== Warehouses =====
@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Warehouse).order_by(Warehouse.id))
    return result.scalars().all()


@router.post("/warehouses", response_model=WarehouseResponse, status_code=201)
async def create_warehouse(
    data: WarehouseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wh = Warehouse(**data.model_dump())
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return wh
