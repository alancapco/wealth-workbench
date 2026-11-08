"""Application configuration with safe defaults for deterministic boot."""
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RM Workbench"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = ""
    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    DATABASE_URL: Optional[str] = None
    EXPECTED_SCHEMA_HEAD: Optional[str] = None

    # Integration credentials are optional at boot; adapters report their own state.
    TIGER_CLIENT_ID: str = ""
    TIGER_PRIVATE_KEY: str = ""
    TIGER_ACCOUNT: str = ""
    TIGER_LICENSE: str = "TBHK"
    TIGER_ENV: str = "PROD"
    TIGER_TOKEN: str = ""
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4-turbo-preview"
    MARKET_NEWS_API_KEY: str = ""
    ALPHAVANTAGE_API_KEY: str = ""
    FREECURRENCY_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    SHARIAH_TOOLS_PATH: str = "/tmp"

    AAOIFI_PDF_PATH: str = ""
    SHARIAH_DEC05_ENABLED: bool = False

    AUTH_MODE: str = "oidc"
    OIDC_ISSUER_URL: str = ""
    OIDC_CLIENT_ID: str = ""
    OIDC_CLIENT_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def reject_fixture_in_production(self) -> "Settings":
        if self.APP_ENV.lower() == "production" and self.AUTH_MODE.lower() == "fixture":
            raise ValueError("AUTH_MODE=fixture is not allowed when APP_ENV=production")
        return self

    @property
    def identity_configured(self) -> bool:
        if self.AUTH_MODE.lower() == "fixture":
            return self.APP_ENV.lower() in {"local", "test", "development"}
        return bool(self.OIDC_ISSUER_URL and self.OIDC_CLIENT_ID and self.OIDC_CLIENT_SECRET)

    @property
    def database_configured(self) -> bool:
        return bool(self.DATABASE_URL and self.DATABASE_URL.strip())

    @property
    def provider_configuration(self) -> dict[str, str]:
        return {
            "market_data": "UNAVAILABLE" if self.TIGER_CLIENT_ID and self.TIGER_PRIVATE_KEY and self.TIGER_ACCOUNT else "UNCONFIGURED",
            "llm": "UNAVAILABLE" if self.LLM_API_KEY else "UNCONFIGURED",
        }


settings = Settings()
