from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext

from src.models.schemas import (
    UserCreateDTO,
    UserResponseDTO,
    UserUpdateDTO,
    RoleEnumDTO,
)
from src.web.api.auth import api_user_dependency
from src.data.dependencies import async_db_dependency

import src.services.users as users_service

router = APIRouter(prefix="/api/users", tags=["users"])
bcrypt_context = CryptContext(schemes=["bcrypt"])


@router.get("/", response_model=list[UserResponseDTO])
async def get_users(
    db: async_db_dependency,
    current_user: api_user_dependency,
) -> list[UserResponseDTO]:
    if current_user.role == RoleEnumDTO.admin:
        users = await users_service.get_all_users(db)
        return users

    else:
        current_user = await users_service.get_user_by_id(current_user.id, db)
        return [current_user]


@router.get("/{user_id}", response_model=UserResponseDTO)
async def get_user_by_id(
    user_id: int,
    db: async_db_dependency,
    current_user: api_user_dependency,
) -> UserResponseDTO:
    if (current_user.id != user_id) and current_user.role != RoleEnumDTO.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user",
        )

    user = await users_service.get_user_by_id(user_id, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.post("/", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_user(
    new_user: UserCreateDTO,
    db: async_db_dependency,
    current_user: api_user_dependency,
) -> UserResponseDTO:

    if not await users_service.check_email_free(new_user.email, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    if not await users_service.check_username_free(new_user.username, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists",
        )

    if new_user.role == RoleEnumDTO.admin and current_user.role != RoleEnumDTO.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create new admin users",
        )

    new_user = await users_service.create_user(new_user, db)

    return new_user


@router.post(
    "/register",
    response_model=UserResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    new_user: UserCreateDTO,
    db: async_db_dependency,
) -> UserResponseDTO:

    if not await users_service.check_email_free(new_user.email, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    if not await users_service.check_username_free(new_user.username, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists",
        )

    created_user = await users_service.create_user(new_user, db)

    return created_user


# Обновление данных пользователя
@router.put("/{user_id}", response_model=UserResponseDTO)
async def update_user(
    user_id: int,
    updated_user: UserUpdateDTO,
    db: async_db_dependency,
    current_user: api_user_dependency,
) -> UserResponseDTO:
    if current_user.id != user_id and current_user.role != RoleEnumDTO.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user",
        )

    old_user = await users_service.get_user_by_id(user_id, db)

    if old_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if updated_user.new_username and updated_user.new_username != old_user.username:
        if not await users_service.check_username_free(updated_user.new_username, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists",
            )

    if updated_user.new_email and updated_user.new_email != old_user.email:
        if not await users_service.check_email_free(updated_user.new_email, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    if updated_user.new_role:
        if current_user.role != RoleEnumDTO.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can modify role",
            )

    return await users_service.update_user(old_user.id, updated_user, db)


# Удаление пользователя
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: async_db_dependency,
    current_user_: api_user_dependency,
):
    if current_user_.role != RoleEnumDTO.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users",
        )

    await users_service.delete_user(user_id, db)
