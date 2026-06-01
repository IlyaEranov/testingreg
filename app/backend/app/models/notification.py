import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    return_request_id: Mapped[int] = mapped_column(
        ForeignKey("return_requests.id", ondelete="CASCADE")
    )
    recipient_type: Mapped[str] = mapped_column(String(20))  # client / employee
    recipient_contact: Mapped[str] = mapped_column(String(255))
    channel: Mapped[str] = mapped_column(String(20))  # sms / email
    message: Mapped[str] = mapped_column(Text)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
