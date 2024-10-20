from .base import Base
from .message import MessageORM

import enum
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship


class RoleEnumORM(enum.Enum):
    user = "user"
    admin = "admin"


class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    telegram_url = Column(String, nullable=True)
    hashed_password = Column(String)
    role = Column(Enum(RoleEnumORM), default=RoleEnumORM.user)

    sent_messages = relationship(
        "MessageORM", foreign_keys=[MessageORM.sender_id], back_populates="sender"
    )
    received_messages = relationship(
        "MessageORM", foreign_keys=[MessageORM.recipient_id], back_populates="recipient"
    )
