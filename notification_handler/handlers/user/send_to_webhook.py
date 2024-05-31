from typing import Any

import aiohttp
from aiogram import Bot, types

from notification_handler.data import config
from notification_handler.keyboards.inline.callbacks import SendToWebhook


async def post_with_headers(url: str, data: dict[str, Any]) -> str:
    headers = {"Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session, session.post(url, json=data, headers=headers) as response:
        return await response.text()


async def send_to_webhook(callback_query: types.CallbackQuery, callback_data: SendToWebhook, bot: Bot) -> None:
    data = {"asd": 2}
    r = await post_with_headers(callback_data.url, data)
    await bot.send_message(config.CHAT_ID, f"Запрос на вебхук был отправлен, текст ответа <b>{r}</b>")
    await callback_query.answer()
