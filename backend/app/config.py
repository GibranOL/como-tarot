from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ─── Database ─────────────────────────────────────────────────────────────
    # We use PostgresDsn for strict URL validation.
    # We do NOT provide a default for production safety.
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string (e.g., postgresql://user:pass@host:port/db)",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure the URL starts with postgresql:// or postgres://"""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string.")
        return v

    # ─── Supabase ─────────────────────────────────────────────────────────────
    SUPABASE_URL: str = Field(..., description="Project URL from Supabase dashboard")
    SUPABASE_ANON_KEY: str = Field(..., description="Anon key for client-side auth")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Service role key for admin tasks")

    # ─── Gemini ───────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = Field(..., description="Google Gemini 2.0 API Key")

    # ─── RevenueCat ───────────────────────────────────────────────────────────
    REVENUECAT_WEBHOOK_SECRET: str = Field(
        "", 
        description="Webhook secret from RevenueCat for validating payment notifications"
    )

    # ─── App Settings ─────────────────────────────────────────────────────────
    APP_ENV: str = Field("development", pattern="^(development|staging|production)$")
    APP_SECRET_KEY: str = Field(..., min_length=16)

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Prevent using the default 'change-me' string in non-development environments."""
        if info.data.get("APP_ENV") != "development" and v in ("change-me", "change-this-to-a-random-secret-key"):
            raise ValueError("APP_SECRET_KEY must be a secure random string in production.")
        return v


# This will raise a ValidationError immediately if the environment is not correctly configured.
settings = Settings()
