import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import settings and metadata
from app.core.config import settings
from app.core.database import Base
# Import all models to ensure they register on Base.metadata
from app import models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Dynamically set the database URL from settings.
# Escape '%' to '%%' to prevent ConfigParser from trying to interpolate password percentages.
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URI).replace("%", "%%"))


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = str(settings.DATABASE_URI)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Event listener to intercept and type-cast parameters in query strings before execution.
# This prevents AmbiguousParameterError from asyncpg due to untyped parameter select statements.
from sqlalchemy import event
from sqlalchemy.engine import Engine
import re

@event.listens_for(Engine, "before_cursor_execute", retval=True)
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if "INSERT INTO permissions" in statement:
        # Cast parameters explicitly to VARCHAR to resolve asyncpg type ambiguity
        statement = re.sub(
            r"SELECT\s+\$1,\s+\$2,\s+\$3,\s+\$4",
            "SELECT $1::varchar, $2::varchar, $3::varchar, $4::varchar",
            statement
        )
    return statement, parameters


def do_run_migrations(connection) -> None:
    """Helper to run migrations using a synchronous connection inside the async context."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an AsyncEngine and run migrations."""
    connectable = create_async_engine(
        str(settings.DATABASE_URI),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

