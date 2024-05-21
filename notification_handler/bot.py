import asyncio

import aiojobs
import orjson
from aiogram import Bot, Dispatcher
from aiogram.client.telegram import TelegramAPIServer
from aiohttp import web

from notification_handler import handlers, utils, web_handlers
from notification_handler.data import config
from notification_handler.db.db import create_db_and_tables
from notification_handler.middlewares import StructLoggingMiddleware


def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(handlers.user.prepare_router())


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.outer_middleware(StructLoggingMiddleware(logger=dp["aiogram_logger"]))


def setup_logging(dp: Dispatcher) -> None:
    dp["aiogram_logger"] = utils.logging.setup_logger().bind(type="aiogram")
    dp["db_logger"] = utils.logging.setup_logger().bind(type="db")
    dp["cache_logger"] = utils.logging.setup_logger().bind(type="cache")
    dp["business_logger"] = utils.logging.setup_logger().bind(type="business")


async def setup_aiogram(dp: Dispatcher) -> None:
    setup_logging(dp)
    logger = dp["aiogram_logger"]
    logger.debug("Configuring aiogram")
    await create_db_and_tables()
    setup_handlers(dp)
    setup_middlewares(dp)
    logger.info("Configured aiogram")


async def aiohttp_on_startup(app: web.Application) -> None:
    dp: Dispatcher = app["dp"]
    workflow_data = {"app": app, "dispatcher": dp}
    if "bot" in app:
        workflow_data["bot"] = app["bot"]
    await dp.emit_startup(**workflow_data)


async def aiohttp_on_shutdown(app: web.Application) -> None:
    dp: Dispatcher = app["dp"]
    for i in [app, *app._subapps]:  # noqa: SLF001 # dirty
        if "scheduler" in i:
            scheduler: aiojobs.Scheduler = i["scheduler"]
            scheduler._closed = True  # noqa: SLF001
            while scheduler.pending_count != 0:
                dp["aiogram_logger"].info(
                    f"Waiting for {scheduler.pending_count} tasks to complete",
                )
                await asyncio.sleep(1)
    workflow_data = {"app": app, "dispatcher": dp}
    if "bot" in app:
        workflow_data["bot"] = app["bot"]
    await dp.emit_shutdown(**workflow_data)


async def aiogram_on_startup_webhook(dispatcher: Dispatcher, bot: Bot) -> None:
    await setup_aiogram(dispatcher)
    webhook_logger = dispatcher["aiogram_logger"].bind(
        webhook_url=config.MAIN_WEBHOOK_ADDRESS,
    )
    webhook_logger.debug("Configuring webhook")
    await bot.set_webhook(
        url=config.MAIN_WEBHOOK_ADDRESS.format(
            token=config.BOT_TOKEN,
            bot_id=config.BOT_TOKEN.split(":")[0],
        ),
        drop_pending_updates=True,
        allowed_updates=dispatcher.resolve_used_update_types(),
        secret_token=config.MAIN_WEBHOOK_SECRET_TOKEN,
    )
    webhook_logger.info("Configured webhook")


async def aiogram_on_shutdown_webhook(dispatcher: Dispatcher, bot: Bot) -> None:
    dispatcher["aiogram_logger"].debug("Stopping webhook")
    await bot.session.close()
    await dispatcher.storage.close()
    dispatcher["aiogram_logger"].info("Stopped webhook")


async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await setup_aiogram(dispatcher)
    dispatcher["aiogram_logger"].info("Started polling")


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    dispatcher["aiogram_logger"].debug("Stopping polling")
    await bot.session.close()
    await dispatcher.storage.close()
    dispatcher["aiogram_logger"].info("Stopped polling")


async def setup_aiohttp_app(  # noqa: RUF029
    bot: Bot,
    dp: Dispatcher,
) -> web.Application:
    scheduler = aiojobs.Scheduler()
    app = web.Application()
    subapps: list[tuple[str, web.Application]] = [
        ("/app/webhooks/", web_handlers.app_webhooks),
        ("/tg/webhooks/", web_handlers.tg_updates_app),
    ]
    for prefix, subapp in subapps:
        subapp["bot"] = bot
        subapp["dp"] = dp
        subapp["scheduler"] = scheduler
        app.add_subapp(prefix, subapp)
    app["bot"] = bot
    app["dp"] = dp
    app["scheduler"] = scheduler
    app.on_startup.append(aiohttp_on_startup)
    app.on_shutdown.append(aiohttp_on_shutdown)
    return app


def main() -> None:
    aiogram_session_logger = utils.logging.setup_logger().bind(type="aiogram_session")

    if config.USE_CUSTOM_API_SERVER:
        session = utils.smart_session.SmartAiogramAiohttpSession(
            api=TelegramAPIServer(
                base=config.CUSTOM_API_SERVER_BASE,
                file=config.CUSTOM_API_SERVER_FILE,
                is_local=config.CUSTOM_API_SERVER_IS_LOCAL,
            ),
            json_loads=orjson.loads,
            logger=aiogram_session_logger,
        )
    else:
        session = utils.smart_session.SmartAiogramAiohttpSession(
            json_loads=orjson.loads,
            logger=aiogram_session_logger,
        )
    bot = Bot(config.BOT_TOKEN, parse_mode="HTML", session=session)

    dp = Dispatcher()
    dp["aiogram_session_logger"] = aiogram_session_logger

    if config.USE_WEBHOOK:
        dp.startup.register(aiogram_on_startup_webhook)
        dp.shutdown.register(aiogram_on_shutdown_webhook)
        web.run_app(
            asyncio.run(setup_aiohttp_app(bot, dp)),
            handle_signals=True,
            host=config.MAIN_WEBHOOK_LISTENING_HOST,
            port=config.MAIN_WEBHOOK_LISTENING_PORT,
        )
    else:
        dp.startup.register(aiogram_on_startup_polling)
        dp.shutdown.register(aiogram_on_shutdown_polling)
        asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
