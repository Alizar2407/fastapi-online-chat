from typing import Annotated
from pydantic import ValidationError

from fastapi import (
    APIRouter,
    Query,
    WebSocket,
    WebSocketDisconnect,
    Depends,
)

import src.services.auth as auth_service
import src.services.users as users_service
import src.services.messages as messages_service

from src.models.schemas import UserResponseDTO
from src.data.dependencies import async_db_dependency

from celery_app.tasks import send_telegram_notification


async def get_current_user_ws(token: str = Query(...)):

    payload = auth_service.decode_access_token(token)
    if not payload:
        return None

    try:
        return UserResponseDTO.model_validate(
            {
                "id": payload.get("id"),
                "username": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "telegram_url": payload.get("telegram_link"),
            }
        )

    except ValidationError:
        return None


router = APIRouter(prefix="/ws/messages", tags=["messages"])
ws_user_dependency = Annotated[UserResponseDTO | None, Depends(get_current_user_ws)]

# Словарь для хранения активных подключений
connected_users = {}


@router.websocket("/{user_id}")
async def chat_websocket(
    websocket: WebSocket,
    user_id: int,
    current_user: ws_user_dependency,
    db: async_db_dependency,
):
    await websocket.accept()
    connected_users[current_user.id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            print(
                f"Client#{current_user.id} writes a message to client#{user_id}: {data}"
            )

            message_dto = await messages_service.create_message(
                sender_id=current_user.id,
                recipient_id=user_id,
                text=data,
                db=db,
            )

            sender = await users_service.get_user_by_id(message_dto.sender_id, db)
            recipient = await users_service.get_user_by_id(message_dto.recipient_id, db)

            message_data = {}
            message_data["text"] = message_dto.text
            message_data["sender_name"] = sender.username
            message_data["timestamp"] = message_dto.timestamp.isoformat()

            if sender.id in connected_users:
                await connected_users[sender.id].send_json(message_data)

            if recipient.id in connected_users:
                await connected_users[recipient.id].send_json(message_data)
            else:
                if recipient.telegram_url:
                    send_telegram_notification.delay(
                        recipient.telegram_url,
                        sender.username,
                        message_data["text"],
                    )

    except WebSocketDisconnect:
        del connected_users[current_user.id]
