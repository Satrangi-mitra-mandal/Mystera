from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://detective:secret@localhost:5432/detectiveos"
    ANTHROPIC_API_KEY: str = ""
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080
    REDIS_URL: str = "redis://localhost:6379"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
