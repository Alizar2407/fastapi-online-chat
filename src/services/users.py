from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth import bcrypt_context

from src.models.user import UserORM, RoleEnumORM
from src.models.message import MessageORM
from src.models.schemas import (
    UserResponseDTO,
    UserUpdateDTO,
    UserCreateDTO,
    RoleEnumDTO,
)


async def check_username_free(username: str, db: AsyncSession) -> bool:
    result = await db.execute(select(UserORM).where(UserORM.username == username))
    return result.scalars().first() is None


async def check_email_free(email: str, db: AsyncSession) -> bool:
    result = await db.execute(select(UserORM).where(UserORM.email == email))
    return result.scalars().first() is None


async def get_all_users(db: AsyncSession) -> list[UserResponseDTO]:
    result = await db.execute(select(UserORM))
    user_models = result.scalars().all()

    return [UserResponseDTO.model_validate(user.__dict__) for user in user_models]


async def get_user_by_id(user_id: int, db: AsyncSession) -> UserResponseDTO | None:
    user_model = await db.execute(select(UserORM).where(UserORM.id == user_id))
    user_model = user_model.scalars().first()

    if user_model:
        return UserResponseDTO.model_validate(user_model.__dict__)

    return None


async def get_user_by_username(
    username: str, db: AsyncSession
) -> UserResponseDTO | None:
    user_model = await db.execute(select(UserORM).where(UserORM.username == username))
    user_model = user_model.scalars().first()

    if user_model:
        return UserResponseDTO.model_validate(user_model.__dict__)

    return None


async def get_connected_users(user_id: int, db: AsyncSession) -> list[UserResponseDTO]:
    subquery = await db.execute(
        select(MessageORM.sender_id).filter(MessageORM.recipient_id == user_id)
    )
    sender_ids = subquery.scalars().all()

    subquery = await db.execute(
        select(MessageORM.recipient_id).filter(MessageORM.sender_id == user_id)
    )
    recipient_ids = subquery.scalars().all()

    unique_ids = set(sender_ids) | set(recipient_ids)

    connected_user_models = await db.execute(
        select(UserORM)
        .filter(UserORM.id.in_(unique_ids))
        .filter(UserORM.id != user_id)
        .distinct()
    )
    connected_user_models = connected_user_models.scalars().all()

    return [
        UserResponseDTO.model_validate(user.__dict__) for user in connected_user_models
    ]


async def create_user(
    user: UserCreateDTO,
    db: AsyncSession,
) -> UserResponseDTO:

    new_user_model = UserORM(
        username=user.username,
        email=user.email,
        telegram_url=user.telegram_url,
        hashed_password=bcrypt_context.hash(user.password),
        role=RoleEnumORM.admin if user.role == RoleEnumDTO.admin else RoleEnumORM.user,
    )
    db.add(new_user_model)

    await db.commit()
    await db.refresh(new_user_model)

    return UserResponseDTO.model_validate(new_user_model.__dict__)


async def update_user(
    user_id: int,
    updated_user: UserUpdateDTO,
    db: AsyncSession,
) -> UserResponseDTO | None:
    user_model = await db.execute(select(UserORM).where(UserORM.id == user_id))
    user_model = user_model.scalars().first()

    if updated_user.new_username:
        user_model.username = updated_user.new_username

    if updated_user.new_email:
        user_model.email = updated_user.new_email

    if updated_user.new_telegram_url:
        user_model.telegram_url = updated_user.new_telegram_url

    if updated_user.new_password:
        user_model.hashed_password = bcrypt_context.hash(updated_user.new_password)

    if updated_user.new_role:
        user_model.role = (
            RoleEnumORM.admin
            if updated_user.new_role == RoleEnumDTO.admin
            else RoleEnumORM.user
        )

    await db.commit()
    await db.refresh(user_model)

    return UserResponseDTO.model_validate(user_model.__dict__)


async def delete_user(user_id: int, db: AsyncSession) -> UserResponseDTO | None:
    user_model = await db.execute(select(UserORM).where(UserORM.id == user_id))
    user_model = user_model.scalars().first()

    if not user_model:
        return None

    await db.delete(user_model)
    await db.commit()

    return UserResponseDTO.model_validate(user_model.__dict__)
