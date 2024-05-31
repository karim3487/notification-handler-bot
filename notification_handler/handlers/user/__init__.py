from aiogram import Router
from aiogram.filters import CommandStart, StateFilter

from notification_handler import states
from notification_handler.filters import ChatTypeFilter, TextFilter
from notification_handler.keyboards.inline.callbacks import SendToWebhook

from . import send_to_webhook, start


def prepare_router() -> Router:
    user_router = Router()
    user_router.message.filter(ChatTypeFilter("private"))

    user_router.message.register(start.start, CommandStart())
    user_router.message.register(
        start.start,
        TextFilter("🏠В главное меню"),  # noqa: RUF001
        StateFilter(states.user.UserMainMenu.menu),
    )

    user_router.callback_query.register(send_to_webhook.send_to_webhook, SendToWebhook.filter())

    return user_router
