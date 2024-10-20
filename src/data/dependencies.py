from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database import session_factory, async_session_factory


def get_db():
    try:
        db = session_factory()
        yield db
    finally:
        db.close()


async def get_db_async() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as db:
        yield db


db_dependency = Annotated[Session, Depends(get_db)]
async_db_dependency = Annotated[AsyncSession, Depends(get_db_async)]
