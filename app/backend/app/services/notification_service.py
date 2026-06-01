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
