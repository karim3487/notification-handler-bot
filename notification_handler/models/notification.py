
from pydantic import Field

from notification_handler.db.models.notification import Statuses
from notification_handler.models.base import BaseModel


class NotificationSchema(BaseModel):
    id: int = Field(None)
    message_id: int | None = Field(None)
    text: str
    url: str
    status: Statuses = Field(Statuses.FREE.value)


