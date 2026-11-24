"""Application configuration with safe defaults for deterministic boot."""
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "WM Workbench"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = ""
    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3005",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3005",
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
    # English news: Newsfilter v2 first, Yahoo Finance RSS when Newsfilter is down.
    NEWSFILTER_API_KEY: str = ""
    NEWS_PROVIDER: str = "newsfilter_yahoo"
    YAHOO_NEWS_DEFAULT_SYMBOLS: str = "^GSPC,^HSI,^STI,HSBC,0700.HK,D05.SI,AAPL"
    ALPHAVANTAGE_API_KEY: str = ""
    FREECURRENCY_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    SHARIAH_TOOLS_PATH: str = "/tmp"

    AAOIFI_PDF_PATH: str = ""
    SHARIAH_DEC05_ENABLED: bool = False

    # DEC-06 / DEC-07 pilot gates. These used to be hardcoded `False` function
    # arguments in the family endpoints, which made every relationships and
    # family-graph request return 503 with no way to enable them. They are now
    # real settings: enabled by default for this demo, and overridable via env
    # (FAMILY_DEC06_ENABLED=false / HOUSEHOLD_DEC07_ENABLED=false).
    FAMILY_DEC06_ENABLED: bool = True
    HOUSEHOLD_DEC07_ENABLED: bool = True

    # Wealth knowledge graph. Disabled automatically when the bolt port is down.
    NEO4J_ENABLED: bool = True
    NEO4J_URI: str = "bolt://localhost:7688"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"

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
    def news_provider(self) -> str:
        value = (self.NEWS_PROVIDER or "newsfilter_yahoo").strip().lower()
        if value in {"newsfilter", "yahoo", "newsfilter_yahoo"}:
            return value
        return "newsfilter_yahoo"

    @property
    def market_news_configured(self) -> bool:
        provider = self.news_provider
        has_newsfilter = bool((self.NEWSFILTER_API_KEY or "").strip())
        if provider in {"yahoo", "newsfilter_yahoo"}:
            return True
        return has_newsfilter

    @property
    def provider_configuration(self) -> dict[str, str]:
        return {
            "market_data": "CONFIGURED" if self.TIGER_CLIENT_ID and self.TIGER_PRIVATE_KEY and self.TIGER_ACCOUNT else "UNCONFIGURED",
            "market_news": "CONFIGURED" if self.market_news_configured else "UNCONFIGURED",
            "llm": "CONFIGURED" if self.LLM_API_KEY else "UNCONFIGURED",
        }


settings = Settings()
