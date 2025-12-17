from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)