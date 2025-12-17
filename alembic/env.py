import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.core.config import settings
from app.db.base import Base

config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Offline migrations (no DB connection needed)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# Sync migration function (passed to run_sync)
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # auto detect type changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Async migrations (required for async SQLAlchemy)"""
    connectable = create_async_engine(
        settings.DATABASE_URL,  # must be async URL: postgresql+asyncpg://...
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        # run_sync wraps the sync function for async engine
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

# Entry point
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
