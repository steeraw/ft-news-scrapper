from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    START_URL: str = "https://www.ft.com/world"
    USER_AGENT: str = Field(default="ft-scraper/1.0")
    CONCURRENCY: int = 5
    REQUEST_TIMEOUT: int = 20
    RETRY_MAX_ATTEMPTS: int = 3

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

settings = Settings()
