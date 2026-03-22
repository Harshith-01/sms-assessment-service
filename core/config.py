from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed service settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret_key: str | None = None
    secret_key: str | None = None
    access_token_expire_minutes: int = 60

    allowed_origins: str = ""
    allowed_hosts: str = "localhost"

    service_name: str = "assessment-service"

    @property
    def resolved_secret_key(self) -> str:
        """Support both JWT_SECRET_KEY and legacy SECRET_KEY names."""
        secret = self.jwt_secret_key or self.secret_key
        if not secret:
            raise RuntimeError("JWT_SECRET_KEY or SECRET_KEY must be set")
        return secret


settings = Settings()

DATABASE_URL = settings.database_url
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = settings.resolved_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
SERVICE_NAME = settings.service_name

ALLOWED_ORIGINS = [item.strip() for item in settings.allowed_origins.split(",") if item.strip()]
ALLOWED_HOSTS = [item.strip() for item in settings.allowed_hosts.split(",") if item.strip()]
