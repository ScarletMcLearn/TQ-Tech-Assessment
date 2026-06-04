from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    email_source: str = Field(default="mock", alias="EMAIL_SOURCE")
    mock_email_file: str = Field(
        default="./data/mock_emails.json", alias="MOCK_EMAIL_FILE"
    )
    ai_provider: str = Field(default="rules", alias="AI_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    poll_interval_seconds: int = Field(default=30, alias="POLL_INTERVAL_SECONDS")
    database_url: str = Field(default="sqlite:///./data/app.db", alias="DATABASE_URL")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def mock_email_path(self) -> Path:
        configured = Path(self.mock_email_file)
        if configured.is_absolute():
            return configured

        cwd_candidate = Path.cwd() / configured
        if cwd_candidate.exists():
            return cwd_candidate

        backend_root = Path(__file__).resolve().parents[1]
        return backend_root / configured


@lru_cache
def get_settings() -> Settings:
    return Settings()
