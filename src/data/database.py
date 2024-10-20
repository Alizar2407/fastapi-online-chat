from src.config import app_settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


engine = create_engine(app_settings.DATABASE_CONNECTION_URL)
async_engine = create_async_engine(app_settings.ASYNC_DATABASE_CONNECTION_URL)

session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
async_session_factory = async_sessionmaker(
    bind=async_engine, autocommit=False, autoflush=False
)
