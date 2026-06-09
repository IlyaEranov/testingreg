from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ReturnRequest
from app.models.user import User
from app.utils.deps import get_current_user

router = APIRouter()


def _short(r: ReturnRequest) -> dict:
    return {
        "id": r.id,
        "number": r.number,
        "client_name": r.client.name if r.client else "",
        "status": r.status,
        "return_type": r.return_type,
        "total_amount": float(r.total_amount or 0),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Role-specific dashboard data."""
    role = current_user.role.name

    base = select(ReturnRequest).options(selectinload(ReturnRequest.client))

    # Count by status
    status_result = await db.execute(
        select(ReturnRequest.status, func.count(ReturnRequest.id))
        .group_by(ReturnRequest.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    total_result = await db.execute(select(func.count(ReturnRequest.id)))
    total = total_result.scalar() or 0

    amount_result = await db.execute(select(func.coalesce(func.sum(ReturnRequest.total_amount), 0)))
    total_amount = float(amount_result.scalar() or 0)

    data = {
        "role": role,
        "role_label": {
            "admin": "Администратор", "manager": "Менеджер",
            "claims": "Сотрудник претензионного отдела",
            "director": "Руководитель", "logistics": "Логистика",
        }.get(role, role),
        "user_name": current_user.full_name,
        "total": total,
        "total_amount": total_amount,
        "by_status": by_status,
        "widgets": [],
        "queue": [],
        "queue_title": "",
    }

    # Менеджер: свои заявки + те, что ждут его решения
    if role == "manager":
        q = await db.execute(
            base.where(ReturnRequest.manager_id == current_user.id)
            .order_by(ReturnRequest.created_at.desc())
        )
        my = q.scalars().all()
        my_active = [r for r in my if r.status not in ("done", "rejected")]
        # Заявки, требующие действия менеджера: заключение получено или товар принят
        decision = [r for r in my if r.status in ("factory_done", "received")]
        data["widgets"] = [
            {"label": "Мои заявки", "value": len(my), "accent": "brand"},
            {"label": "В работе", "value": len(my_active), "accent": "amber"},
            {"label": "Требуют решения", "value": len(decision), "accent": "purple"},
            {"label": "Завершено", "value": len([r for r in my if r.status == "done"]), "accent": "green"},
        ]
        data["queue_title"] = "Заявки, требующие вашего решения"
        data["queue"] = [_short(r) for r in decision]

    elif role == "claims":
        claims_stages = ["client_data", "claim_factory", "factory_review", "factory_done", "in_transit", "received"]
        q = await db.execute(
            base.where(ReturnRequest.status.in_(claims_stages))
            .order_by(ReturnRequest.created_at.asc())
        )
        active = q.scalars().all()
        data["widgets"] = [
            {"label": "Ожидают данных", "value": by_status.get("client_data", 0), "accent": "amber"},
            {"label": "На рассмотрении завода", "value": by_status.get("claim_factory", 0) + by_status.get("factory_review", 0), "accent": "orange"},
            {"label": "Приёмка на складе", "value": by_status.get("in_transit", 0), "accent": "purple"},
            {"label": "Всего в работе", "value": len(active), "accent": "brand"},
        ]
        data["queue_title"] = "Заявки претензионного отдела"
        data["queue"] = [_short(r) for r in active]

    elif role == "logistics":
        q = await db.execute(
            base.where(ReturnRequest.status == "in_transit")
            .order_by(ReturnRequest.created_at.asc())
        )
        to_deliver = q.scalars().all()
        data["widgets"] = [
            {"label": "К перевозке", "value": len(to_deliver), "accent": "amber"},
            {"label": "Всего заявок", "value": total, "accent": "brand"},
        ]
        data["queue_title"] = "Заявки к перевозке на склад"
        data["queue"] = [_short(r) for r in to_deliver]

    elif role == "director":
        q = await db.execute(
            base.where(ReturnRequest.status.in_(["factory_done", "received"]))
            .order_by(ReturnRequest.created_at.asc())
        )
        approval = q.scalars().all()
        active = total - by_status.get("done", 0) - by_status.get("rejected", 0)
        data["widgets"] = [
            {"label": "Требуют решения", "value": len(approval), "accent": "purple"},
            {"label": "Всего заявок", "value": total, "accent": "brand"},
            {"label": "В работе", "value": active, "accent": "amber"},
            {"label": "Сумма возвратов", "value": round(total_amount, 2), "accent": "green", "is_money": True},
        ]
        data["queue_title"] = "Заявки, требующие решения"
        data["queue"] = [_short(r) for r in approval]

    else:  # admin
        active = total - by_status.get("done", 0) - by_status.get("rejected", 0)
        users_count = await db.execute(select(func.count(User.id)))
        data["widgets"] = [
            {"label": "Всего заявок", "value": total, "accent": "brand"},
            {"label": "В работе", "value": active, "accent": "amber"},
            {"label": "Завершено", "value": by_status.get("done", 0), "accent": "green"},
            {"label": "Пользователей", "value": users_count.scalar() or 0, "accent": "purple"},
        ]
        q = await db.execute(
            base.order_by(ReturnRequest.created_at.desc()).limit(8)
        )
        data["queue_title"] = "Последние заявки"
        data["queue"] = [_short(r) for r in q.scalars().all()]

    return data
