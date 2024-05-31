from aiogram import F, Router
from aiogram.filters import Command

from notification_handler.filters import ChatTypeFilter

from . import get_chat_id


def prepare_router() -> Router:
    group_router = Router()
    group_router.message.filter(
        ChatTypeFilter(["group", "supergroup"]),
        F.text,
    )

    group_router.message.register(
        get_chat_id.get_chat_id,
        Command("get_chat_id"),
    )

    return group_router
