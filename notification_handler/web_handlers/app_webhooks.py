import json
import secrets
from typing import TYPE_CHECKING

import aiohttp.web
from aiohttp import web
from pydantic import ValidationError

from notification_handler.data import config
from notification_handler.data.config import CHAT_ID
from notification_handler.db.services.notification import NotificationService
from notification_handler.keyboards.inline.send_to_webhook import YesOrNoKb
from notification_handler.models.notification import NotificationSchema
from notification_handler.utils.messages import NEW_TASK, UPDATE_TASK

if TYPE_CHECKING:
    import aiojobs
    from aiogram import Bot

app_webhooks = web.Application()


async def validate_request(req: web.Request) -> NotificationSchema:
    if not secrets.compare_digest(
            req.headers.get("X-Telegram-Bot-Api-Secret-Token", ""),
            config.MAIN_WEBHOOK_SECRET_TOKEN,
    ):
        raise aiohttp.web.HTTPNotFound
    if not secrets.compare_digest(req.match_info["bot_id"], config.BOT_ID):
        raise aiohttp.web.HTTPNotFound

    if not await req.text():
        raise aiohttp.web.HTTPBadRequest

    scheduler: aiojobs.Scheduler = req.app["scheduler"]
    if scheduler.pending_count > 100:
        raise web.HTTPTooManyRequests
    if scheduler.closed:
        raise web.HTTPServiceUnavailable(reason="Closed queue")

    try:
        notification = NotificationSchema.model_validate_json(await req.text())
    except ValidationError as err:
        error_response = {
            "error": {
                "message": str(err),
            },
        }
        raise aiohttp.web.HTTPBadRequest(text=json.dumps(error_response), content_type="application/json") from err

    return notification


async def update_notification_and_send_message(req: web.Request, exist_notification: NotificationSchema,
                                               new_notification: NotificationSchema) -> None:
    bot: Bot = req.app["bot"]

    await NotificationService.update_notification(exist_notification.id, new_notification.model_dump())
    notification = await NotificationService.get_notification_by_id(exist_notification.id)
    if not notification:
        await bot.send_message(chat_id=CHAT_ID, text="Не удалось найти notification с таким ID")  # noqa: RUF001
        return

    msg_text = UPDATE_TASK.format(
        text=notification.text,
        url=notification.url,
        status=notification.status.value,
    )
    if notification.with_keyboard:
        msg = await bot.send_message(
            CHAT_ID,
            msg_text,
            reply_to_message_id=exist_notification.message_id,
            reply_markup=YesOrNoKb.yes_or_no(),
            disable_notification=True
        )
    else:
        msg = await bot.send_message(
            CHAT_ID,
            msg_text,
            disable_notification=True
        )

    notification.message_id = msg.message_id
    await NotificationService.update_notification(notification.id, notification.model_dump())


async def save_notification_and_send_message(req: web.Request, notification: NotificationSchema) -> None:
    bot: Bot = req.app["bot"]

    await NotificationService.insert_new(notification)

    msg_text = NEW_TASK.format(
        text=notification.text,
        url=notification.url,
        status=notification.status.value,
    )

    if notification.with_keyboard:
        msg = await bot.send_message(
            CHAT_ID,
            msg_text,
            reply_markup=YesOrNoKb.yes_or_no(),
            disable_notification=True
        )
    else:
        msg = await bot.send_message(
            CHAT_ID,
            msg_text,
            disable_notification=True
        )
    notification.message_id = msg.message_id
    await NotificationService.update_notification(notification.id, notification.model_dump())


async def execute(req: web.Request) -> web.Response:
    new_notification = await validate_request(req)

    exist_notification = await NotificationService.get_notification_by_id(new_notification.id)
    if exist_notification:
        await update_notification_and_send_message(req, exist_notification, new_notification)
    else:
        await save_notification_and_send_message(req, new_notification)
    return web.Response(status=201)


app_webhooks.add_routes(
    [web.post("/bot/{bot_id}", execute)],
)
