from pydantic_settings import BaseSettings, SettingsConfigDict


class CeleryApplicationSettings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    CELERY_BROKER_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


celery_app_settings = CeleryApplicationSettings()
