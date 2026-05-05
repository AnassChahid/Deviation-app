from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Port Deviation Management API"
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    enable_api_docs: bool = False
    auto_create_database: bool = False
    run_startup_migrations: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        weak_values = {"change-me", "change-me-for-testing", "replace-me", "secret"}
        if value.lower() in weak_values or len(value) < 32:
            raise ValueError("SECRET_KEY must be a strong value with at least 32 characters")
        return value


settings = Settings()
