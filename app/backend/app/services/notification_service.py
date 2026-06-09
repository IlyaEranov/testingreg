"""Service for creating notifications during return lifecycle."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    return_request_id: int,
    recipient_type: str,
    recipient_contact: str,
    message: str,
    channel: str = "email",
) -> Notification:
    """Create a notification (simulated send)."""
    notification = Notification(
        return_request_id=return_request_id,
        recipient_type=recipient_type,
        recipient_contact=recipient_contact,
        channel=channel,
        message=message,
        is_sent=True,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    await db.flush()
    return notification


# Статус → шаблон уведомления покупателю
STATUS_MESSAGES = {
    "client_data": "По заявке №{number} просим направить сведения о товаре, причину и материалы (фото/видео).",
    "claim_factory": "По заявке №{number} оформлена претензия и направлена заводу-изготовителю.",
    "in_transit": "Товар по заявке №{number} принят к перевозке на склад магазина.",
    "rejected": "К сожалению, возврат по заявке №{number} отклонён. Подробности у менеджера.",
    "done": "Обработка заявки №{number} завершена. Направляем акт сверки.",
}


# Событие заявки → (список адресатов, текст уведомления сотруднику).
# Адресат: "manager" — ответственному менеджеру заявки;
#          "role:<role>" — всем сотрудникам указанной роли.
EMPLOYEE_EVENTS = {
    "created": (["role:director"],
                "Зарегистрирована новая заявка на возврат №{number}."),
    "client_data": (["role:claims"],
                    "Заявка №{number}: ожидаются данные покупателя, требуется обработка претензии."),
    "claim_factory": (["role:director"],
                      "По заявке №{number} направлена претензия заводу-изготовителю."),
    "factory_review": (["role:director"],
                       "Заявка №{number} передана заводу на экспертизу."),
    "factory_done": (["manager", "role:director"],
                     "По заявке №{number} получено заключение завода, требуется решение."),
    "in_transit": (["role:logistics", "role:claims"],
                   "Заявка №{number}: сформирован маршрутный лист, требуется перевозка на склад."),
    "received": (["manager", "role:director"],
                 "Товар по заявке №{number} принят и сверён, требуется решение."),
    "rejected": (["manager", "role:director"],
                 "Возврат по заявке №{number} отклонён."),
    "done": (["manager", "role:director"],
             "Обработка заявки №{number} завершена."),
}


async def notify_employees(db: AsyncSession, return_request, event: str):
    """Создать внутрисистемные уведомления сотрудникам по событию заявки.

    Одно событие может адресоваться нескольким получателям (например,
    менеджеру заявки и всем руководителям).
    """
    cfg = EMPLOYEE_EVENTS.get(event)
    if not cfg:
        return None
    targets, template = cfg
    message = template.format(number=return_request.number)
    for target in targets:
        if target == "manager":
            recipient_user_id, recipient_role = return_request.manager_id, None
        elif target.startswith("role:"):
            recipient_user_id, recipient_role = None, target.split(":", 1)[1]
        else:
            continue
        db.add(Notification(
            return_request_id=return_request.id,
            recipient_type="employee",
            recipient_contact="",
            channel="system",
            message=message,
            is_sent=True,
            sent_at=datetime.now(timezone.utc),
            recipient_user_id=recipient_user_id,
            recipient_role=recipient_role,
        ))
    await db.flush()


async def notify_client_on_status(
    db: AsyncSession, return_request, new_status: str
):
    """Send client notification on status change if a template exists."""
    template = STATUS_MESSAGES.get(new_status)
    if not template:
        return None

    contact = ""
    if return_request.client:
        contact = return_request.client.phone or return_request.client.email or ""

    message = template.format(number=return_request.number)
    return await create_notification(
        db,
        return_request_id=return_request.id,
        recipient_type="client",
        recipient_contact=contact,
        message=message,
        channel="sms" if (return_request.client and return_request.client.phone) else "email",
    )
