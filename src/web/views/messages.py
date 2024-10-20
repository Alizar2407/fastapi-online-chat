from fastapi import APIRouter, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.web.views.auth import views_user_dependency
from src.data.dependencies import async_db_dependency

import src.services.users as users_service
import src.services.messages as messages_service


router = APIRouter(prefix="/messages", tags=["messages"])
templates = Jinja2Templates(directory="src/frontend/templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def chat_page(
    request: Request,
    current_user: views_user_dependency,
    db: async_db_dependency,
):
    if not current_user:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    all_users = await users_service.get_all_users(db)
    chat_users = await users_service.get_connected_users(current_user.id, db)

    return templates.TemplateResponse(
        "users_list.html",
        {
            "request": request,
            "user": current_user,
            "all_users": all_users,
            "chat_users": chat_users,
        },
    )


@router.get("/start-chat", response_class=HTMLResponse, include_in_schema=False)
async def start_chat(
    request: Request,
    username: str,
    current_user: views_user_dependency,
    db: async_db_dependency,
):
    if not current_user:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user = await users_service.get_user_by_username(username, db)

    if user:
        return RedirectResponse(
            url=f"/messages/{user.id}", status_code=status.HTTP_302_FOUND
        )

    return RedirectResponse(url="/messages", status_code=status.HTTP_302_FOUND)


@router.get("/{user_id}", response_class=HTMLResponse, include_in_schema=False)
async def user_chat(
    request: Request,
    user_id: int,
    current_user: views_user_dependency,
    db: async_db_dependency,
):
    if not current_user:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    messages = await messages_service.get_messages_between_users(
        current_user.id, user_id, db
    )

    other_user = await users_service.get_user_by_id(user_id, db)
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user": current_user,
            "other_user": other_user,
            "messages": messages,
        },
    )


@router.post("/{user_id}", response_class=HTMLResponse, include_in_schema=False)
async def send_message(
    user_id: int,
    request: Request,
    current_user: views_user_dependency,
    db: async_db_dependency,
):
    form = await request.form()
    message_content = form.get("text")

    new_message = await messages_service.create_message(
        sender_id=current_user.id,
        recipient_id=user_id,
        text=message_content,
        db=db,
    )

    return RedirectResponse(
        url=f"/messages/{user_id}", status_code=status.HTTP_302_FOUND
    )
