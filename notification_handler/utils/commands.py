from aiogram import Bot, types


async def set_default_commands(bot: Bot) -> None:
    default_commands = [
        types.BotCommand(command="start", description="Запуск бота"),
        types.BotCommand(command="help", description="Помощь"),
        types.BotCommand(command="get_chat_id", description="Получить ID чата"),
    ]
    await bot.set_my_commands(
        default_commands,
        scope=types.BotCommandScopeAllPrivateChats(),
    )
