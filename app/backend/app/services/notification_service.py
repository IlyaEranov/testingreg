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


# Status → client notification message templates
STATUS_MESSAGES = {
    "warehouse": "Ваша заявка №{number} принята в обработку и передана на проверку склада.",
    "expertise": "Товар по заявке №{number} передан поставщику на экспертизу.",
    "approved": "Возврат по заявке №{number} одобрен. Денежные средства будут возвращены.",
    "rejected": "К сожалению, возврат по заявке №{number} отклонён. Подробности у менеджера.",
    "done": "Обработка заявки №{number} завершена. Денежные средства возвращены.",
}


# Событие заявки → (список адресатов, текст уведомления сотруднику).
# Адресат: "manager" — ответственному менеджеру заявки;
#          "role:<role>" — всем сотрудникам указанной роли.
EMPLOYEE_EVENTS = {
    "created": (["role:director"],
                "Зарегистрирована новая заявка на возврат №{number}."),
    "warehouse": (["role:warehouse_staff"],
                  "Новая заявка №{number} поступила на складскую проверку."),
    "waiting": (["manager", "role:director"],
                "Заявка №{number} прошла складскую проверку и ожидает решения."),
    "expertise": (["role:director"],
                  "Заявка №{number} передана поставщику на экспертизу."),
    "expertise_done": (["manager", "role:director"],
                       "Экспертиза по заявке №{number} завершена, требуется решение."),
    "approved": (["manager", "role:director"],
                 "Возврат по заявке №{number} одобрен."),
    "rejected": (["manager", "role:director"],
                 "Возврат по заявке №{number} отклонён."),
    "done": (["manager", "role:director"],
             "Возврат по заявке №{number} завершён."),
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
