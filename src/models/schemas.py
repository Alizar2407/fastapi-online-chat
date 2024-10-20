from pydantic import BaseModel
from datetime import datetime


import enum
from typing import Optional
from pydantic import BaseModel, EmailStr


class RoleEnumDTO(str, enum.Enum):
    user = "user"
    admin = "admin"


class UserCreateDTO(BaseModel):
    username: str
    email: EmailStr
    telegram_url: Optional[str] = None
    password: str  # not hashed
    role: Optional[RoleEnumDTO] = RoleEnumDTO.user

    class Config:
        model_config = {"from_attributes": True}


class UserUpdateDTO(BaseModel):
    new_username: Optional[str] = None
    new_email: Optional[EmailStr] = None
    new_telegram_url: Optional[str] = None
    new_password: Optional[str] = None  # not hashed
    new_role: Optional[RoleEnumDTO] = None

    class Config:
        model_config = {"from_attributes": True}


class UserResponseDTO(BaseModel):
    id: int
    username: str
    email: EmailStr
    telegram_url: Optional[str] = None
    role: RoleEnumDTO

    class Config:
        model_config = {"from_attributes": True}


class MessageCreateDTO(BaseModel):
    recipient_id: int
    text: str

    class Config:
        model_config = {"from_attributes": True}


class MessageResponseDTO(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    text: str
    timestamp: datetime

    class Config:
        model_config = {"from_attributes": True}


class TokenDTO(BaseModel):
    access_token: str
    token_type: str
