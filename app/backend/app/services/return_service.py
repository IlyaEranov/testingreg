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


# Допустимые переходы статусов: {текущий: {новый: [роли]}}.
# Процесс: обращение → проверка условий → сбор данных от покупателя →
#   (ветка «брак»: претензия заводу → экспертиза/заключение) →
#   транспортировка на склад → приёмка и сверка → решение (списание/корректировка).
STATUS_TRANSITIONS = {
    "created": {
        "client_data": ["manager", "admin"],                 # условия соблюдены
        "rejected": ["manager", "director", "admin"],          # условия не соблюдены
    },
    "client_data": {
        "claim_factory": ["claims", "admin"],                  # ветка А (брак): претензия заводу
        "in_transit": ["claims", "manager", "admin"],          # ветка Б (надлежащее качество)
    },
    "claim_factory": {
        "factory_review": ["claims", "admin"],                 # завод проводит экспертизу
        "factory_done": ["claims", "admin"],                   # завод подтвердил по данным
    },
    "factory_review": {
        "factory_done": ["claims", "admin"],
    },
    "factory_done": {
        "in_transit": ["manager", "claims", "admin"],          # брак подтверждён → к перевозке
        "rejected": ["manager", "director", "admin"],          # нарушение эксплуатации → отказ
    },
    "in_transit": {
        "received": ["claims", "admin"],                       # приёмка и сверка на складе
    },
    "received": {
        "done": ["manager", "admin"],                          # решение: списание / корректировка
    },
}


async def generate_number(db: AsyncSession) -> str:
    result = await db.execute(select(func.count(ReturnRequest.id)))
    count = result.scalar() or 0
    return f"ВЗ-{count + 1:06d}"


async def create_return_request(
    db: AsyncSession, data: ReturnRequestCreate, user: User
) -> ReturnRequest:
    # Найти или создать клиента
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

    total = sum(Decimal(str(item.price)) * item.quantity for item in data.items)

    number = await generate_number(db)
    return_request = ReturnRequest(
        number=number,
        client_id=client.id,
        return_type=data.return_type,
        kind=data.kind,
        reason_id=data.reason_id,
        status="created",
        manager_id=user.id,
        warehouse_id=data.warehouse_id,
        comment=data.comment,
        total_amount=total,
    )
    db.add(return_request)
    await db.flush()

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

    db.add(ActionHistory(
        return_request_id=return_request.id,
        user_id=user.id,
        action="Обращение зарегистрировано, проверяются условия возврата",
        new_status="created",
    ))
    await notify_employees(db, return_request, "created")

    await db.commit()
    await db.refresh(return_request)
    return return_request


async def transition_status(
    db: AsyncSession, return_id: int, new_status: str,
    user: User, comment: str | None = None, outcome: str | None = None
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
        raise ValueError(f"Недопустимый переход: {rr.status} → {new_status}")

    allowed_roles = allowed[new_status]
    if "system" not in allowed_roles:
        user_role = user.role.name if user.role else ""
        if user_role not in allowed_roles:
            raise PermissionError("Недостаточно прав для данного перехода")

    # Решение по результату возврата требует указания итога (списание/корректировка)
    if new_status == "done":
        if outcome not in ("write_off", "correction"):
            raise ValueError("Не указан итог обработки: списание или корректировка")
        rr.outcome = outcome

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

    # Побочные эффекты переходов
    if new_status == "in_transit":
        # Сформировать маршрутный лист для отдела логистики
        await generate_and_save_document(db, rr, "route_sheet")
        db.add(ActionHistory(
            return_request_id=rr.id, user_id=None,
            action="Сформирован маршрутный лист, заявка передана в отдел логистики",
            old_status=new_status, new_status=new_status,
        ))

    if new_status == "rejected":
        await generate_and_save_document(db, rr, "rejection_notice")
        db.add(ActionHistory(
            return_request_id=rr.id, user_id=None,
            action="Сформировано уведомление об отказе",
            old_status=new_status, new_status=new_status,
        ))

    if new_status == "done":
        label = "списание" if outcome == "write_off" else "корректировка"
        db.add(ActionHistory(
            return_request_id=rr.id, user_id=None,
            action=f"Принято решение: {label}; операция и акт сверки поставлены в очередь обмена с 1С",
            old_status=new_status, new_status=new_status,
        ))

    # Внутрисистемные уведомления сотрудникам по событию
    await notify_employees(db, rr, new_status)

    await db.commit()

    # Уведомление покупателя — через очередь (Celery), с резервной синхронной отправкой
    enqueued = enqueue_notification(rr.id, new_status)
    if not enqueued:
        await notify_client_on_status(db, rr, new_status)
        await db.commit()

    # Обмен с 1С — только при финальном решении (списание / корректировка)
    if new_status == "done":
        enqueue_onec_sync(rr.id)

    await db.refresh(rr)
    return rr


async def submit_warehouse_check(
    db: AsyncSession, return_id: int,
    checks: list[WarehouseCheckCreate], user: User
) -> ReturnRequest:
    """Приёмка и сверка товара на складе сотрудником претензионного отдела
    (переход «Транспортировка на склад» → «Принят и сверён»)."""
    result = await db.execute(
        select(ReturnRequest).where(ReturnRequest.id == return_id)
    )
    rr = result.scalar_one_or_none()
    if not rr:
        raise ValueError("Заявка не найдена")
    if rr.status != "in_transit":
        raise ValueError("Принять и сверить можно только заявку в статусе «Транспортировка на склад»")

    for check_data in checks:
        check = WarehouseCheck(
            return_item_id=check_data.return_item_id,
            quantity_fact=check_data.quantity_fact,
            packaging_condition=check_data.packaging_condition,
            defect_description=check_data.defect_description,
            inspector_id=user.id,
        )
        db.add(check)

    # Акт осмотра/сверки формируется при приёмке
    await generate_and_save_document(db, rr, "inspection_act")

    rr.status = "received"
    db.add(ActionHistory(
        return_request_id=rr.id,
        user_id=user.id,
        action="Товар принят и сверён с заявкой, сформирован акт осмотра",
        old_status="in_transit",
        new_status="received",
    ))
    await notify_employees(db, rr, "received")

    await db.commit()
    await db.refresh(rr)
    return rr


async def send_claim_to_factory(
    db: AsyncSession, return_id: int, supplier_id: int,
    user: User, details: str | None = None
) -> SupplierExamination:
    """Сформировать претензию и направить её заводу-изготовителю
    (переход «Ожидает данных покупателя» → «Претензия отправлена заводу»)."""
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
    if rr.status != "client_data":
        raise ValueError("Направить претензию можно только после получения данных от покупателя")

    rr.status = "claim_factory"

    claim = SupplierExamination(
        return_request_id=return_id,
        supplier_id=supplier_id,
        transfer_date=datetime.now(timezone.utc),
        details=details,
    )
    db.add(claim)

    # Претензионное письмо формирует АИС
    await generate_and_save_document(db, rr, "claim_letter")

    db.add(ActionHistory(
        return_request_id=rr.id,
        user_id=user.id,
        action="Сформирована и направлена претензия заводу-изготовителю",
        old_status="client_data",
        new_status="claim_factory",
    ))

    await notify_client_on_status(db, rr, "claim_factory")
    await notify_employees(db, rr, "claim_factory")

    await db.commit()
    await db.refresh(claim)
    return claim


async def submit_factory_result(
    db: AsyncSession, return_id: int,
    conclusion: str, details: str | None, user: User
) -> ReturnRequest:
    """Внести заключение завода (переход «Претензия отправлена заводу» или
    «На рассмотрении завода» → «Заключение получено»).

    conclusion: defect_confirmed | misuse | transport_damage
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(ReturnRequest).where(ReturnRequest.id == return_id)
    )
    rr = result.scalar_one_or_none()
    if not rr or rr.status not in ("claim_factory", "factory_review"):
        raise ValueError("Заявка не найдена или не находится на рассмотрении завода")

    claim_result = await db.execute(
        select(SupplierExamination)
        .where(SupplierExamination.return_request_id == return_id)
        .order_by(SupplierExamination.id.desc())
    )
    claim = claim_result.scalar_one_or_none()
    if claim:
        claim.conclusion = conclusion
        claim.details = details
        claim.result_date = datetime.now(timezone.utc)

    rr.status = "factory_done"

    db.add(ActionHistory(
        return_request_id=rr.id,
        user_id=user.id,
        action=f"Получено заключение завода: {conclusion}",
        old_status=rr.status if rr.status != "factory_done" else "claim_factory",
        new_status="factory_done",
        details=details,
    ))
    await notify_employees(db, rr, "factory_done")

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
        "kind": rr.kind,
        "outcome": rr.outcome,
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
