from enum import Enum as PyEnum

from sqlalchemy import Column, Enum, Integer, Text

from notification_handler.db.models.base import Base


class Statuses(PyEnum):
    OCCUPIED = "occupied"
    FREE = "free"
    DONE = "done"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, unique=True)
    message_id = Column(Integer, unique=True, nullable=True)
    text = Column(Text)
    url = Column(Text)
    status = Column(Enum(Statuses), default=Statuses.FREE)
