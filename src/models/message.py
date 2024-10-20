from .base import Base

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class MessageORM(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(Integer, ForeignKey("users.id"))
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    sender = relationship(
        "UserORM", foreign_keys=[sender_id], back_populates="sent_messages"
    )
    recipient = relationship(
        "UserORM", foreign_keys=[recipient_id], back_populates="received_messages"
    )
