from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ReturnRequest, ReturnItem, SupplierExamination
from app.models.directory import ReturnReason, Supplier
from app.models.user import User
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/summary")
async def get_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Overall statistics."""
    query = select(ReturnRequest)
    if date_from:
        query = query.where(ReturnRequest.created_at >= date_from)
    if date_to:
        query = query.where(ReturnRequest.created_at <= date_to + "T23:59:59")

    result = await db.execute(query)
    returns = result.scalars().all()

    total = len(returns)
    by_status = {}
    total_amount = 0
    for r in returns:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        total_amount += float(r.total_amount or 0)

    active = total - by_status.get("done", 0) - by_status.get("rejected", 0)

    return {
        "total": total,
        "active": active,
        "done": by_status.get("done", 0),
        "rejected": by_status.get("rejected", 0),
        "total_amount": round(total_amount, 2),
        "by_status": by_status,
    }


@router.get("/by-reason")
async def report_by_reason(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(
            ReturnReason.name,
            func.count(ReturnRequest.id).label("count"),
            func.coalesce(func.sum(ReturnRequest.total_amount), 0).label("amount"),
        )
        .join(ReturnRequest, ReturnRequest.reason_id == ReturnReason.id)
        .group_by(ReturnReason.name)
    )
    if date_from:
        query = query.where(ReturnRequest.created_at >= date_from)
    if date_to:
        query = query.where(ReturnRequest.created_at <= date_to + "T23:59:59")

    result = await db.execute(query)
    rows = result.all()
    return [{"reason": r[0], "count": r[1], "amount": float(r[2])} for r in rows]


@router.get("/by-month")
async def report_by_month(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    month_expr = func.to_char(ReturnRequest.created_at, "YYYY-MM")
    query = (
        select(
            month_expr.label("month"),
            func.count(ReturnRequest.id).label("count"),
            func.coalesce(func.sum(ReturnRequest.total_amount), 0).label("amount"),
        )
        .group_by(month_expr)
        .order_by(month_expr)
    )
    if date_from:
        query = query.where(ReturnRequest.created_at >= date_from)
    if date_to:
        query = query.where(ReturnRequest.created_at <= date_to + "T23:59:59")

    result = await db.execute(query)
    rows = result.all()
    return [{"month": r[0], "count": r[1], "amount": float(r[2])} for r in rows]


@router.get("/by-supplier")
async def report_by_supplier(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(
            Supplier.name,
            func.count(SupplierExamination.id).label("exams"),
            func.count(
                case((SupplierExamination.conclusion == "defect_confirmed", 1))
            ).label("defects"),
        )
        .join(SupplierExamination, SupplierExamination.supplier_id == Supplier.id)
        .group_by(Supplier.name)
        .order_by(func.count(SupplierExamination.id).desc())
    )
    result = await db.execute(query)
    rows = result.all()
    return [
        {"supplier": r[0], "examinations": r[1], "defects_confirmed": r[2]}
        for r in rows
    ]
