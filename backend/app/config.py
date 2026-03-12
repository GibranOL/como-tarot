from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql://localhost/cosmotarot"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Gemini
    GEMINI_API_KEY: str = ""

    # RevenueCat
    REVENUECAT_WEBHOOK_SECRET: str = ""

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"


settings = Settings()
