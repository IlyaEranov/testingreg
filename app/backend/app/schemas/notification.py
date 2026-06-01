from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    return_request_id: int
    recipient_type: str
    recipient_contact: str
    channel: str
    message: str
    is_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True
