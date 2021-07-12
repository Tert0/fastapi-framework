from os import getenv
from typing import TypeVar, Dict

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.future import select as sa_select
from sqlalchemy.orm import DeclarativeMeta, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import Executable
from sqlalchemy.sql.expression import exists as sa_exists, delete as sa_delete, Delete
from sqlalchemy.sql.functions import count
from sqlalchemy.sql.selectable import Select, Exists

from .logger import get_logger

load_dotenv()

T = TypeVar("T")


def select(entity) -> Select:
    """Shortcut for :meth:`sqlalchemy.future.select`"""

    return sa_select(entity)


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

    def __init__(self, driver: str, options: Dict = {"pool_size": 20, "max_overflow": 20}, **kwargs):
        url: str = URL.create(drivername=driver, **kwargs)
        self._engine = create_async_engine(url, echo=True, pool_pre_ping=True, pool_recycle=300, **options)
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

    async def commit(self):
        """Commits/Saves changes to Database"""
        await self._session.commit()


logger = get_logger(__name__)

DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = getenv("DB_PORT", "5432")
DB_DATABASE = getenv("DB_DATABASE")
DB_USERNAME = getenv("DB_USERNAME", "postgres")
DB_PASSWORD = getenv("DB_PASSWORD", "")
DB_POOL_SIZE = getenv("DB_POOL_SIZE", "20")
DB_MAX_OVERFLOW = getenv("DB_MAX_OVERFLOW", "20")
DB_POOL = True if getenv("DB_POOL", "True").lower() == "true" else False


class DatabaseDependency:
    db: DB
    database_url_options: Dict
    engine_options: Dict
    initialised: bool = False

    def __init__(self):
        self.database_url_options = {
            "host": DB_HOST,
            "port": DB_PORT,
            "database": DB_DATABASE,
            "username": DB_USERNAME,
            "password": DB_PASSWORD,
        }
        self.database_url_options = dict([(k, v) for k, v in self.database_url_options.items() if v != ""])
        self.engine_options: Dict = {
            "pool_size": DB_POOL_SIZE,
            "max_overflow": DB_MAX_OVERFLOW,
            "poolclass": DB_POOL,
        }
        self.engine_options = dict([(k, int(v)) for k, v in self.engine_options.items() if v != ""])
        if self.engine_options["poolclass"] == 0:
            self.engine_options["poolclass"] = NullPool
        else:
            del self.engine_options["poolclass"]
        self.db = DB(
            getenv("DB_DRIVER", "postgresql+asyncpg"), options=self.engine_options, **self.database_url_options
        )
        logger.info("Connected to Database")

    async def init(self) -> None:
        if self.initialised:
            return
        logger.info("Create Tables")
        self.initialised = True
        await self.db.create_tables()

    async def __call__(self) -> DB:
        if not self.initialised:
            await self.init()
        return self.db


database_dependency: DatabaseDependency = DatabaseDependency()
Base: DeclarativeMeta = database_dependency.db.Base
