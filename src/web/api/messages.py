from typing import List
from fastapi import APIRouter, HTTPException, status

from src.web.api.auth import api_user_dependency
from src.models.schemas import MessageCreateDTO, MessageResponseDTO
from src.data.dependencies import async_db_dependency

import src.services.users as users_service
import src.services.messages as messages_service


router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/", response_model=List[MessageResponseDTO])
async def get_all_dialog_messages(
    db: async_db_dependency,
    current_user: api_user_dependency,
) -> list[MessageResponseDTO]:
    return await messages_service.get_user_dialog_messages(current_user.id, db)


@router.post(
    "/",
    response_model=MessageResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    new_message: MessageCreateDTO,
    db: async_db_dependency,
    current_user: api_user_dependency,
) -> MessageResponseDTO:
    user = await users_service.get_user_by_id(current_user.id, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={new_message.recipient_id} not found",
        )

    return await messages_service.create_message(
        sender_id=current_user.id,
        recipient_id=new_message.recipient_id,
        text=new_message.text,
        db=db,
    )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    db: async_db_dependency,
    current_user: api_user_dependency,
):
    message = await messages_service.get_message_by_id(message_id, db)

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages",
        )

    await messages_service.delete_messages(message_id, db)
