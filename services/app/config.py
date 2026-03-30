from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BOOMA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Booma Prototype API"
    jwt_secret: str = "prototype-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    refresh_token_expire_days: int = 30
    sqlite_path: Path = Path(__file__).resolve().parent.parent / "data" / "booma.db"
    synthetic_data_path: Path = Path(__file__).resolve().parents[2] / "references" / "data" / "synthetic-data.json"
    prototype_password: str = "demo"
    # Comma-separated browser origins allowed to call the API (CORS). Default matches Vite dev/preview on port 9000.
    cors_origins: str = "http://localhost:9000,http://127.0.0.1:9000"
    # Logging: DEBUG, INFO, WARNING, ERROR (see BOOMA_LOG_LEVEL in .env)
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def strip_cors(cls, v: str) -> str:
        return (v or "").strip()


settings = Settings()
