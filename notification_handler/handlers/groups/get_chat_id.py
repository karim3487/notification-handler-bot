from aiogram import html, types


async def get_chat_id(msg: types.Message) -> None:
    cid = str(msg.chat.id)

    await msg.answer(f"ID чата: {html.bold(html.quote(cid))}")
