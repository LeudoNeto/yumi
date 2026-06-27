from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """Application settings, override via environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Yumi"
    # Default targets the docker-compose MySQL service. Override with DATABASE_URL.
    database_url: str = "mysql+pymysql://yumi:yumipass@db:3306/yumi"

    # Auth
    secret_key: str = "change-me-in-production-please-use-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # one week

    # CORS — comma separated list of allowed origins for the SPA
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Public base url used when building absolute links (e.g. the storefront url)
    public_base_url: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
