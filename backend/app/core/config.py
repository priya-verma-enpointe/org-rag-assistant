from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Organization Knowledge Assistant"
    DATABASE_URL: str
    GEMINI_API_KEY: str
    API_KEY: str = "default_secret_key_123"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )

settings = Settings()
