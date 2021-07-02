import asyncio
from asyncio import get_event_loop
from os import getenv
from typing import TypeVar, Optional, Type, Union

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.future import select as sa_select
from sqlalchemy.orm import DeclarativeMeta, declarative_base, selectinload, sessionmaker
from sqlalchemy.sql import Executable
from sqlalchemy.sql.expression import exists as sa_exists, delete as sa_delete, Delete
from sqlalchemy.sql.functions import count
from sqlalchemy.sql.selectable import Select, Exists

from .logger import get_logger
from .modules import disabled_modules

load_dotenv()

T = TypeVar("T")


def select(entity, *args) -> Select:
    """Shortcut for :meth:`sqlalchemy.future.select`"""
    if not args:
        return sa_select(entity)

    options = []
    for arg in args:
        if isinstance(arg, (tuple, list)):
            head, *tail = arg
            opt = selectinload(head)
            for x in tail:
                opt = opt.selectinload(x)
            options.append(opt)
        else:
            options.append(selectinload(arg))

    return sa_select(entity).options(*options)


def filter_by(cls, *args, **kwargs) -> Select:
    """Shortcut for :meth:`sqlalchemy.future.Select.filter_by`"""
    return select(cls, *args).filter_by(**kwargs)


def exists(*entities, **kwargs) -> Exists:
    """Shortcut for :meth:`sqlalchemy.sql.expression.exists`"""
    return sa_exists(*entities, **kwargs)


def delete(table) -> Delete:
    """Shortcut for :meth:`sqlalchemy.sql.expression.delete`"""
    return sa_delete(table)


class DB:
    """An async SQLAlchemy ORM wrapper"""

    Base: DeclarativeMeta
    _engine: AsyncEngine
    _session: AsyncSession

    def __init__(self, driver: str, host: str, port: str, database: str, username: str, password: str):
        self._engine = create_async_engine(
            URL(
                drivername=driver,
                host=host,
                port=port,
                database=database,
                username=username,
                password=password,
            ),
            echo=True,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=20,
            max_overflow=20,
        )
        self.Base = declarative_base()
        self._session: AsyncSession = sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)()

    async def create_tables(self):
        """Creates all Model Tables"""
        async with self._engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.create_all)

    async def add(self, obj: T) -> T:
        """Adds an Row to the Database"""
        self._session.add(obj)
        return obj

    async def delete(self, obj: T) -> T:
        """Deletes a Row from the Database"""
        await self._session.delete(obj)
        return obj

    async def exec(self, statement: Executable, *args, **kwargs):
        """Executes a SQL Statement"""
        return await self._session.execute(statement, *args, **kwargs)

    async def stream(self, statement: Executable, *args, **kwargs):
        """Returns an Stream of Query Results"""
        return (await self._session.stream(statement, *args, **kwargs)).scalars()

    async def all(self, statement: Executable, *args, **kwargs) -> list[T]:
        """Returns all matches for a Query"""
        return [x async for x in await self.stream(statement, *args, **kwargs)]

    async def first(self, *args, **kwargs):
        """Returns first match for a Query"""
        return (await self.exec(*args, **kwargs)).scalar()

    async def exists(self, *args, **kwargs):
        """Checks if there is a match for this Query"""
        return await self.first(exists(*args, **kwargs).select())

    async def count(self, *args, **kwargs):
        """Counts matches for a Query"""
        return await self.first(select(count()).select_from(*args, **kwargs))

    async def get(self, cls: Type[T], *args, **kwargs) -> Optional[T]:
        """Returns first element of the Query from filter_by(cls, *args, **kwargs)"""
        return await self.first(filter_by(cls, *args, **kwargs))

    async def commit(self):
        """Commits/Saves changes to Database"""
        await self._session.commit()


db: Union[DB, None] = None
if "database" not in disabled_modules:
    logger = get_logger(__name__)

    db: DB = DB(
        getenv("DB_DRIVER", "postgresql+asyncpg"),
        getenv("DB_HOST", "localhost"),
        getenv("DB_PORT", "5432"),
        getenv("DB_DATABASE"),
        getenv("DB_USERNAME", "postgres"),
        getenv("DB_PASSWORD", ""),
    )

    logger.info("Connected to Database")

    loop = get_event_loop()
    logger.info("Create Tables")
    asyncio.ensure_future(db.create_tables())
