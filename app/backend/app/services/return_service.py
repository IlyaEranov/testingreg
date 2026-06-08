from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ReturnRequest, ReturnItem, Client, ActionHistory,
    WarehouseCheck, SupplierExamination, Document
)
from app.models.user import User
from app.schemas.return_request import ReturnRequestCreate, WarehouseCheckCreate
from app.services.notification_service import notify_client_on_status, notify_employees
from app.services.document_service import generate_and_save_document

import logging

logger = logging.getLogger(__name__)


def enqueue_notification(return_request_id: int, new_status: str):
    """Поместить задание на уведомление покупателя в очередь (Celery/Redis).

    Бэкенд бизнес-логики не отправляет уведомление сам, а кладёт задание
    в очередь сообщений — его выполнит обработчик очереди (Celery worker).
    Если брокер недоступен, выполняется резервная синхронная отправка,
    чтобы прототип оставался работоспособным.
    """
    try:
        from app.tasks import send_notification_task
        send_notification_task.delay(return_request_id, new_status)
        return True
    except Exception as exc:
        logger.warning(f"Очередь недоступна, синхронная отправка уведомления: {exc}")
        return False


def enqueue_onec_sync(return_request_id: int):
    """Поместить задание на обмен с 1С в очередь (Celery/Redis)."""
    try:
        from app.tasks import sync_with_onec_task
        sync_with_onec_task.delay(return_request_id)
        return True
    except Exception as exc:
        logger.warning(f"Очередь недоступна, обмен с 1С отложен: {exc}")
        return False

# Valid status transitions: {current_status: {new_status: [allowed_roles]}}
STATUS_TRANSITIONS = {
    "created": {
        "warehouse": ["manager", "admin"],
    },
    "warehouse": {
        "waiting": ["warehouse_staff", "admin"],
    },
    "waiting": {
        "approved": ["manager", "director", "admin"],
        "rejected": ["manager", "director", "admin"],
        "expertise": ["manager", "admin"],
    },
    "expertise": {
        "expertise_done": ["manager", "admin"],
    },
    "expertise_done": {
        "approved": ["manager", "director", "admin"],
        "rejected": ["manager", "director", "admin"],
    },
    "approved": {
        "docs": ["system", "admin"],
    },
    "docs": {
        "finance": ["system", "admin"],
    },
    "finance": {
        "done": ["manager", "admin"],
    },
}


async def generate_number(db: AsyncSession) -> str:
    result = await db.execute(select(func.count(ReturnRequest.id)))
    count = result.scalar() or 0
    return f"ВЗ-{count + 1:06d}"


async def create_return_request(
    db: AsyncSession, data: ReturnRequestCreate, user: User
) -> ReturnRequest:
    # Find or create client
    result = await db.execute(
        select(Client).where(Client.name == data.client_name)
    )
    client = result.scalar_one_or_none()
    if not client:
        client = Client(
            name=data.client_name,
            phone=data.client_phone,
            email=data.client_email,
        )
        db.add(client)
        await db.flush()

    # Calculate total
    total = sum(Decimal(str(item.price)) * item.quantity for item in data.items)

    number = await generate_number(db)
    return_request = ReturnRequest(
        number=number,
        client_id=client.id,
        return_type=data.return_type,
        reason_id=data.reason_id,
        status="created",
        manager_id=user.id,
        warehouse_id=data.warehouse_id,
        comment=data.comment,
        total_amount=total,
    )
    db.add(return_request)
    await db.flush()

    # Create items
    for item_data in data.items:
        item = ReturnItem(
            return_request_id=return_request.id,
            product_name=item_data.product_name,
            article=item_data.article,
            quantity=item_data.quantity,
            unit=item_data.unit,
            price=item_data.price,
        )
        db.add(item)

    # Log action
    db.add(ActionHistory(
        return_request_id=return_request.id,
        user_id=user.id,
        action="Заявка создана",
        new_status="created",
    ))
    await notify_employees(db, return_request, "created")

    await db.commit()
    await db.refresh(return_request)
    return return_request


async def transition_status(
    db: AsyncSession, return_id: int, new_status: str,
    user: User, comment: str | None = None
) -> ReturnRequest:
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
        raise ValueError("Заявка не найдена")

    allowed = STATUS_TRANSITIONS.get(rr.status, {})
    if new_status not in allowed:
        raise ValueError(
            f"Недопустимый переход: {rr.status} → {new_status}"
        )

    # Check role (system transitions bypass role check)
    allowed_roles = allowed[new_status]
    if "system" not in allowed_roles:
        user_role = user.role.name if user.role else ""
        if user_role not in allowed_roles:
            raise PermissionError("Недостаточно прав для данного перехода")

    old_status = rr.status
    rr.status = new_status

    action_text = f"Статус изменён: {old_status} → {new_status}"
    if comment:
        action_text += f". {comment}"

    db.add(ActionHistory(
        return_request_id=rr.id,
        user_id=user.id,
        action=action_text,
        old_status=old_status,
        new_status=new_status,
        details=comment,
    ))

    # On transition to warehouse — generate application + route sheet
    if new_status == "warehouse":
        for doc_type in ["application", "route_sheet"]:
            await generate_and_save_document(db, rr, doc_type)
        db.add(ActionHistory(
            return_request_id=rr.id, user_id=None,
            action="Документы сформированы: заявление на возврат, маршрутный лист",
            old_status=new_status, new_status=new_status,
        ))

    # On rejection — generate rejection notice
    if new_status == "rejected":
        await generate_and_save_document(db, rr, "rejection_notice")
        db.add(ActionHistory(
            return_request_id=rr.id, user_id=None,
            action="Сформировано уведомление об отказе",
            old_status=new_status, new_status=new_status,
        ))

    # Внутрисистемное уведомление сотруднику(ам) по событию
    await notify_employees(db, rr, new_status)

    await db.commit()

    # Уведомление покупателя — через очередь сообщений (Celery)
    enqueued = enqueue_notification(rr.id, new_status)
    if not enqueued:
        # Резервная синхронная отправка, если брокер недоступен
        await notify_client_on_status(db, rr, new_status)
        await db.commit()

    # Auto-advance approved → docs → finance
    if new_status == "approved":
        await generate_and_save_document(db, rr, "return_act")
        rr.status = "docs"
        db.add(ActionHistory(
            return_request_id=rr.id,
            user_id=None,
            action="Документы возврата сформированы автоматически",
            old_status="approved",
            new_status="docs",
        ))
        await db.flush()

        rr.status = "finance"
        db.add(ActionHistory(
            return_request_id=rr.id,
            user_id=None,
            action="Заявка передана на финансовое завершение",
            old_status="docs",
            new_status="finance",
        ))
        await db.commit()

    # On financial completion → 1C integration + refund act
    if new_status == "done":
        await generate_and_save_document(db, rr, "refund_act")
        db.add(ActionHistory(
            return_request_id=rr.id, user_id=None,
            action="Акт возврата средств сформирован, обмен с 1С поставлен в очередь",
            old_status="finance", new_status="done",
        ))
        await db.commit()
        # Обмен с 1С — через очередь сообщений (Celery)
        enqueue_onec_sync(rr.id)

    await db.refresh(rr)
    return rr


async def submit_warehouse_check(
    db: AsyncSession, return_id: int,
    checks: list[WarehouseCheckCreate], user: User
) -> ReturnRequest:
    result = await db.execute(
        select(ReturnRequest).where(ReturnRequest.id == return_id)
    )
    rr = result.scalar_one_or_none()
    if not rr:
        raise ValueError("Заявка не найдена")
    if rr.status != "warehouse":
        raise ValueError("Заявка не на проверке склада")

    for check_data in checks:
        check = WarehouseCheck(
            return_item_id=check_data.return_item_id,
            quantity_fact=check_data.quantity_fact,
            packaging_condition=check_data.packaging_condition,
            defect_description=check_data.defect_description,
            inspector_id=user.id,
        )
        db.add(check)

    rr.status = "waiting"
    db.add(ActionHistory(
        return_request_id=rr.id,
        user_id=user.id,
        action="Складская проверка завершена",
        old_status="warehouse",
        new_status="waiting",
    ))
    await notify_employees(db, rr, "waiting")

    await db.commit()
    await db.refresh(rr)
    return rr


async def create_examination(
    db: AsyncSession, return_id: int, supplier_id: int,
    user: User, details: str | None = None
) -> SupplierExamination:
    from datetime import datetime, timezone

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
        raise ValueError("Заявка не найдена")
    if rr.status != "waiting":
        raise ValueError("Передать на экспертизу можно только заявку в статусе «Ожидает решения»")

    rr.status = "expertise"

    exam = SupplierExamination(
        return_request_id=return_id,
        supplier_id=supplier_id,
        transfer_date=datetime.now(timezone.utc),
        details=details,
    )
    db.add(exam)

    # Generate transfer act
    await generate_and_save_document(db, rr, "transfer_act")

    db.add(ActionHistory(
        return_request_id=rr.id,
        user_id=user.id,
        action="Товар передан поставщику на экспертизу, сформирован акт передачи",
        old_status="waiting",
        new_status="expertise",
    ))

    # Notify client
    await notify_client_on_status(db, rr, "expertise")
    # Notify employees (руководителю — товар передан на экспертизу)
    await notify_employees(db, rr, "expertise")

    await db.commit()
    await db.refresh(exam)
    return exam


async def submit_examination_result(
    db: AsyncSession, return_id: int,
    conclusion: str, details: str | None, user: User
) -> ReturnRequest:
    from datetime import datetime, timezone

    result = await db.execute(
        select(ReturnRequest).where(ReturnRequest.id == return_id)
    )
    rr = result.scalar_one_or_none()
    if not rr or rr.status != "expertise":
        raise ValueError("Заявка не найдена или не на экспертизе")

    # Update examination
    exam_result = await db.execute(
        select(SupplierExamination)
        .where(SupplierExamination.return_request_id == return_id)
        .order_by(SupplierExamination.id.desc())
    )
    exam = exam_result.scalar_one_or_none()
    if exam:
        exam.conclusion = conclusion
        exam.details = details
        exam.result_date = datetime.now(timezone.utc)

    rr.status = "expertise_done"

    db.add(ActionHistory(
        return_request_id=rr.id,
        user_id=user.id,
        action=f"Результат экспертизы внесён: {conclusion}",
        old_status="expertise",
        new_status="expertise_done",
        details=details,
    ))
    await notify_employees(db, rr, "expertise_done")

    await db.commit()
    await db.refresh(rr)
    return rr


async def get_return_detail(db: AsyncSession, return_id: int) -> dict | None:
    result = await db.execute(
        select(ReturnRequest)
        .options(
            selectinload(ReturnRequest.client),
            selectinload(ReturnRequest.reason),
            selectinload(ReturnRequest.manager),
            selectinload(ReturnRequest.warehouse),
            selectinload(ReturnRequest.items).selectinload(ReturnItem.warehouse_checks).selectinload(WarehouseCheck.inspector),
            selectinload(ReturnRequest.documents),
            selectinload(ReturnRequest.history).selectinload(ActionHistory.user),
        )
        .where(ReturnRequest.id == return_id)
    )
    rr = result.scalar_one_or_none()
    if not rr:
        return None

    # Get examination
    exam_result = await db.execute(
        select(SupplierExamination)
        .options(selectinload(SupplierExamination.supplier))
        .where(SupplierExamination.return_request_id == return_id)
        .order_by(SupplierExamination.id.desc())
    )
    exam = exam_result.scalar_one_or_none()

    checks = []
    for item in rr.items:
        for check in item.warehouse_checks:
            checks.append({
                "id": check.id,
                "return_item_id": check.return_item_id,
                "quantity_fact": check.quantity_fact,
                "packaging_condition": check.packaging_condition,
                "defect_description": check.defect_description,
                "inspector_name": check.inspector.full_name if check.inspector else None,
                "checked_at": check.checked_at,
            })

    return {
        "id": rr.id,
        "number": rr.number,
        "client_name": rr.client.name if rr.client else "",
        "client_phone": rr.client.phone if rr.client else None,
        "client_email": rr.client.email if rr.client else None,
        "return_type": rr.return_type,
        "reason_name": rr.reason.name if rr.reason else None,
        "status": rr.status,
        "manager_name": rr.manager.full_name if rr.manager else None,
        "warehouse_name": rr.warehouse.name if rr.warehouse else None,
        "comment": rr.comment,
        "total_amount": rr.total_amount,
        "created_at": rr.created_at,
        "updated_at": rr.updated_at,
        "items": [
            {
                "id": i.id, "product_name": i.product_name, "article": i.article,
                "quantity": i.quantity, "unit": i.unit, "price": i.price,
            }
            for i in rr.items
        ],
        "checks": checks,
        "documents": [
            {
                "id": d.id, "document_type": d.document_type,
                "file_name": d.file_name, "file_path": d.file_path,
                "created_at": d.created_at,
            }
            for d in rr.documents
        ],
        "history": [
            {
                "id": h.id, "action": h.action,
                "old_status": h.old_status, "new_status": h.new_status,
                "details": h.details,
                "user_name": h.user.full_name if h.user else "Система",
                "created_at": h.created_at,
            }
            for h in sorted(rr.history, key=lambda x: x.created_at)
        ],
        "examination": {
            "id": exam.id,
            "supplier_id": exam.supplier_id,
            "supplier_name": exam.supplier.name if exam.supplier else None,
            "transfer_date": exam.transfer_date,
            "result_date": exam.result_date,
            "conclusion": exam.conclusion,
            "details": exam.details,
        } if exam else None,
    }
