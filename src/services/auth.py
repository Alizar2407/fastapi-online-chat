from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import app_settings
from src.models.user import UserORM
from src.models.schemas import UserResponseDTO

ALGORITHM = "HS256"
bcrypt_context = CryptContext(schemes=["bcrypt"])


# Проверка корректности логина и пароля с помощью БД
async def authenticate_user(
    username: str, password: str, db: AsyncSession
) -> UserResponseDTO | None:
    user_model = await db.execute(select(UserORM).where(UserORM.username == username))
    user_model = user_model.scalars().first()

    if user_model and bcrypt_context.verify(password, user_model.hashed_password):
        return UserResponseDTO.model_validate(user_model.__dict__)

    return None


# Создание JWT на основе данных пользователя
def create_access_token(user: UserResponseDTO, expires_delta: timedelta = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=30)

    expires = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": user.username,
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "telegram_link": user.telegram_url,
        "exp": expires,
    }

    return jwt.encode(
        to_encode,
        app_settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )


# Расшифровка JWT с помощью секретного ключа
def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, app_settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
