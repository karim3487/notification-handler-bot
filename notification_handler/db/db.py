from pathlib import Path
from typing import Any

from sqlalchemy import Engine, event, text
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from notification_handler.data.config import DB_NAME
from notification_handler.db.models.base import Base

"""
Imports of these models are needed to correctly create tables in the database.
For more information see https://stackoverflow.com/questions/7478403/sqlalchemy-classes-across-files
"""

url = f"sqlite+aiosqlite:///{DB_NAME}"
data_folder = Path("data")
if data_folder.exists() is False:
    data_folder.mkdir()
engine = create_async_engine(url, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:  # noqa: ARG001
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def check_all_tables_exist(db_engine: AsyncEngine) -> bool:
    async with db_engine.begin() as conn:
        for table in Base.metadata.tables.values():
            result = await conn.execute(
                text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table.name}'"))  # noqa: S608
            if result.scalar() is None:
                return False
    return True


async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        if await check_all_tables_exist(engine):
            pass
        else:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
