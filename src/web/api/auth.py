from typing import Annotated
from datetime import timedelta
from pydantic import ValidationError

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.config import app_settings
from src.models.schemas import UserResponseDTO
from src.data.dependencies import async_db_dependency

import src.services.auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(token: str = Depends(oauth2_bearer)) -> UserResponseDTO:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    payload = auth_service.decode_access_token(token)
    if not payload:
        raise credentials_exception

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
        raise credentials_exception


@router.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: async_db_dependency,
) -> dict:
    user: UserResponseDTO = await auth_service.authenticate_user(
        form_data.username, form_data.password, db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = auth_service.create_access_token(
        user, expires_delta=timedelta(minutes=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


api_user_dependency = Annotated[UserResponseDTO, Depends(get_current_user)]
