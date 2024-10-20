from datetime import timedelta
from pydantic import ValidationError
from typing import Annotated, Optional

from fastapi import APIRouter, Request, Response, Depends, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.config import app_settings
from src.models.schemas import TokenDTO, UserResponseDTO, UserCreateDTO
from src.data.dependencies import async_db_dependency

import src.services.auth as auth_service
import src.services.users as users_service

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="src/frontend/templates")


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")


# Расшифровка jwt и получение данных о пользователе
async def get_current_user(request: Request):

    try:

        token = request.cookies.get("access_token")
        if not token:
            return None

        payload = auth_service.decode_access_token(token)
        if not payload:
            logout(request)

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
            logout(request)

    except Exception as e:
        return None


# Страница входа
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def authentication_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
    )


# Аутентификация пользователя, сохранение jwt в cookie файлах в случае успеха
@router.post("/", response_class=HTMLResponse, include_in_schema=False)
async def login(db: async_db_dependency, request: Request):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()

        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(
            response=response,
            form_data=form,
            db=db,
        )

        if not validate_user_cookie:
            msg = "Incorrect username or password"
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={"msg": msg, "success_flag": False},
            )

        return response

    except Exception as e:
        print("Unknown error", e)

        msg = f"Unknown error"
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"msg": msg, "success_flag": False},
        )


# Страница регистрации
@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
    )


# Регистрация пользователя
@router.post("/register", response_class=HTMLResponse, include_in_schema=False)
async def create_user(
    db: async_db_dependency,
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    telegram_url: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
):
    if not await users_service.check_username_free(username, db):
        msg = "This username is already in use"
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"msg": msg},
        )

    if not await users_service.check_email_free(email, db):
        msg = "This email is already registered"
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"msg": msg},
        )

    if password != password2:
        msg = "Passwords do not match"
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"msg": msg},
        )

    new_user = UserCreateDTO(
        username=username,
        email=email,
        telegram_url=telegram_url,
        password=password,
    )
    await users_service.create_user(new_user, db)

    msg = "User successfully created"
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"msg": msg, "success_flag": True},
    )


# Удаление cookie и переход на страницу аутентификации
@router.get("/logout", response_class=HTMLResponse, include_in_schema=False)
async def logout(request: Request):
    msg = "Logout successful"
    response = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"msg": msg, "success_flag": True},
    )
    response.delete_cookie(key="access_token")
    return response


# Добавление cookie для аутентификации
@router.post("/token", response_model=TokenDTO, include_in_schema=False)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: async_db_dependency,
):
    user: UserResponseDTO = await auth_service.authenticate_user(
        form_data.username, form_data.password, db
    )

    if not user:
        return False

    token = auth_service.create_access_token(
        user, expires_delta=timedelta(minutes=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response.set_cookie(key="access_token", value=token, httponly=False)

    return True


views_user_dependency = Annotated[UserResponseDTO | None, Depends(get_current_user)]
