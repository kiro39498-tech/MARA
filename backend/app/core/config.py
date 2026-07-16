"""Application configuration management."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional
from pydantic import PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Get the base directory (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings and configuration.

    Settings are loaded from environment variables with fallback to .env file.
    """

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Inventory Management System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Production-ready inventory management system with AI forecasting"
    )

    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:5180",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
        "http://127.0.0.1:5180",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from various formats.

        Supports:
        1. JSON array string:
            '["http://localhost:5173","http://localhost:3000"]'
        2. Comma-separated string:
            'http://localhost:5173,http://localhost:3000'
        3. Python list: ["http://localhost:5173", "http://localhost:3000"]
        """
        if isinstance(v, list):
            return v

        if isinstance(v, str):
            # Try parsing as JSON first
            if v.startswith("["):
                import json

                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Failed to parse CORS origins as JSON: {v}"
                    )

            # Fall back to comma-separated
            return [
                origin.strip() for origin in v.split(",") if origin.strip()
            ]

        return v

    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_PASSWORD_RESET_URL: str = (
        "http://localhost:5173/auth/reset-password?token={token}"
    )

    # Database Settings
    POSTGRES_SERVER: str = "localhost"  # Safe default
    POSTGRES_USER: str  # Required - must be in .env
    POSTGRES_PASSWORD: str  # Required - must be in .env
    POSTGRES_DB: str  # Required - must be in .env
    POSTGRES_PORT: int = 5432
    DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        """Assemble database URI from individual components."""
        if isinstance(v, str):
            return v

        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )

    @model_validator(mode="after")
    def validate_critical_settings(self) -> "Settings":
        """Validate that critical database settings are properly configured."""
        # Check for default/weak passwords in production
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be changed in production!")
            if self.POSTGRES_PASSWORD == "postgres":
                raise ValueError(
                    "POSTGRES_PASSWORD must be changed from default!"
                )

        # Log warning for weak passwords in development
        if self.POSTGRES_PASSWORD in ["postgres", "password", "admin", ""]:
            logger.warning(
                f" Using weak database password in {self.ENVIRONMENT} mode"
            )

        return self

    # Redis Settings (for caching and background tasks)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Email Settings (for notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Super Admin Settings
    FIRST_SUPERUSER_EMAIL: str = "admin@inventory.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_DIR: str = "uploads"

    # AI/ML Settings
    AI_MODEL_PATH: str = "models/"
    FORECAST_DAYS: int = 30

    # -------------------------------------------------------------------------
    # Azure OpenAI — LLM provider for MARA Planning Copilot.
    # agent_framework.openai.OpenAIChatClient supports Azure via azure_endpoint
    # + api_version params — no separate Azure class needed.
    #
    # To switch provider later, update only these four env vars.
    # -------------------------------------------------------------------------
    AZURE_OPENAI_ENDPOINT: str = ""        # e.g. https://maqopenai.openai.azure.com/
    AZURE_OPENAI_API_KEY: str = ""         # Azure resource key
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"  # deployment name (used as model)
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"

    # -------------------------------------------------------------------------
    # MCP Planning Server
    # The FastMCP server runs as a background task on this host:port.
    # Agents communicate with it through MCPPlanningClient.
    # -------------------------------------------------------------------------
    MCP_SERVER_HOST: str = "127.0.0.1"
    MCP_SERVER_PORT: int = 8001
    MCP_SERVER_TIMEOUT: float = 30.0

    @property
    def MCP_SERVER_URL(self) -> str:
        """Full base URL for the MCP planning server."""
        return f"http://{self.MCP_SERVER_HOST}:{self.MCP_SERVER_PORT}"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        env_prefix="",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings object

    Raises:
        ValueError: If required settings are missing or invalid
    """
    # Log .env file loading status with absolute path
    abs_env_path = str(ENV_FILE.resolve())
    if ENV_FILE.exists():
        logger.info(f"✓ Loading .env from: {abs_env_path}")
    else:
        logger.warning(f"⚠ .env file not found at: {abs_env_path}")
        logger.warning("Using environment variables or defaults")

    try:
        settings_obj = Settings()
        logger.info(
            "Configuration loaded successfully "
            f"(Environment: {settings_obj.ENVIRONMENT})"
        )

        # Log database connection details (masked password)
        import re

        masked_url = re.sub(
            r"://([^:]+):([^@]+)@",
            r"://\1:****@",
            str(settings_obj.DATABASE_URI),
        )
        logger.info(
            f"Database: postgresql+asyncpg://{settings_obj.POSTGRES_USER}:"
            f"****@{settings_obj.POSTGRES_SERVER}:"
            f"{settings_obj.POSTGRES_PORT}/"
            f"{settings_obj.POSTGRES_DB}"
        )
        logger.info(f"SQLAlchemy URI (masked): {masked_url}")

        return settings_obj
    except Exception as e:
        logger.error(f" Failed to load configuration: {e}")
        raise


settings = get_settings()
