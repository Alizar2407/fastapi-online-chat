from datetime import datetime, timezone
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import UserORM
from src.models.message import MessageORM
from src.models.schemas import MessageResponseDTO


# Получение всех сообщений
async def get_all_messages(db: AsyncSession) -> list[MessageResponseDTO]:
    result = await db.execute(select(MessageORM))
    message_models = result.scalars().all()

    return [
        MessageResponseDTO.model_validate(message.__dict__)
        for message in message_models
    ]


# Получение сообщения по его id
async def get_message_by_id(message_id: int, db: AsyncSession) -> MessageResponseDTO:
    message_model = await db.execute(
        select(MessageORM).where(MessageORM.id == message_id)
    )
    message_model = message_model.scalars().first()

    if message_model:
        return MessageResponseDTO.model_validate(message_model.__dict__)

    return None


# Получение всех отправленных пользователем сообщений по его id
async def get_user_messages(user_id: int, db: AsyncSession) -> list[MessageResponseDTO]:
    user_model = await db.execute(
        select(UserORM)
        .options(joinedload(UserORM.sent_messages))
        .where(UserORM.id == user_id)
    )
    user_model = user_model.scalars().first()

    if not user_model:
        return []

    return [
        MessageResponseDTO.model_validate(message.__dict__)
        for message in user_model.sent_messages
    ]


# Выбор всех сообщений, отправленных пользователю и полученных им
async def get_user_dialog_messages(
    user_id: int, db: AsyncSession
) -> list[MessageResponseDTO]:
    user_model = await db.execute(
        select(UserORM)
        .options(
            joinedload(UserORM.sent_messages),
            joinedload(UserORM.received_messages),
        )
        .where(UserORM.id == user_id)
    )
    user_model = user_model.scalars().first()

    all_messages = user_model.sent_messages + user_model.received_messages

    return [
        MessageResponseDTO.model_validate(message.__dict__) for message in all_messages
    ]


# Добавление сообщения в БД
async def create_message(
    sender_id: int,
    recipient_id: int,
    text: str,
    db: AsyncSession,
) -> MessageResponseDTO:

    message_model = MessageORM(
        sender_id=sender_id,
        recipient_id=recipient_id,
        text=text,
        timestamp=datetime.now(),
    )
    db.add(message_model)

    await db.commit()
    await db.refresh(message_model)

    return MessageResponseDTO.model_validate(message_model.__dict__)


# Получение истории сообщений между двумя пользователями
async def get_messages_between_users(
    first_user_id: int,
    second_user_id: int,
    db: AsyncSession,
) -> list[MessageResponseDTO]:
    result = await db.execute(
        select(MessageORM)
        .filter(
            or_(
                and_(
                    MessageORM.sender_id == first_user_id,
                    MessageORM.recipient_id == second_user_id,
                ),
                and_(
                    MessageORM.sender_id == second_user_id,
                    MessageORM.recipient_id == first_user_id,
                ),
            )
        )
        .order_by(MessageORM.timestamp)
    )
    message_models = result.scalars().all()

    return [
        MessageResponseDTO.model_validate(message.__dict__)
        for message in message_models
    ]


# Удаление сообщения из БД по его id
async def delete_messages(
    message_id: int, db: AsyncSession
) -> MessageResponseDTO | None:
    message_model = await db.execute(
        select(MessageORM).where(MessageORM.id == message_id)
    )
    message_model = message_model.scalars().first()

    if not message_model:
        return None

    await db.delete(message_model)
    await db.commit()

    return MessageResponseDTO.model_validate(message_model.__dict__)
