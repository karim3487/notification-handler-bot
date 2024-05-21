
from sqlalchemy import select, update

from notification_handler.db.db import async_session_maker
from notification_handler.db.models.notification import Notification
from notification_handler.models.base import to_pydantic
from notification_handler.models.notification import NotificationSchema


class NotificationService:
    @staticmethod
    async def insert_new(notification: NotificationSchema) -> int:
        async with async_session_maker() as session:
            new_notification = Notification(**notification.model_dump())
            session.add(new_notification)
            await session.commit()
            await session.refresh(new_notification)
            return new_notification.id

    @staticmethod
    async def get_notification_by_id(notification_id: int) -> NotificationSchema | None:
        async with async_session_maker() as session:
            stmt = select(Notification).where(Notification.id == notification_id).limit(1)
            notification = await session.execute(stmt)
            notification = notification.scalar()
            if not notification:
                return None
            return to_pydantic(notification, NotificationSchema)

    @staticmethod
    async def update_notification(notification_id: int, updated_data: dict) -> None:
        async with async_session_maker() as session:
            stmt = update(Notification).where(Notification.id == notification_id).values(updated_data)
            await session.execute(stmt)
            await session.commit()
