from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "АИС Сопровождение возвратов товаров"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/returns_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/returns_db"

    # JWT
    SECRET_KEY: str = "region-service-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # 1C Integration
    ONEC_API_URL: str = "http://localhost:8081/api"
    ONEC_API_TOKEN: str = ""

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # File storage
    UPLOAD_DIR: str = "uploads"
    DOCUMENTS_DIR: str = "documents"

    class Config:
        env_file = ".env"


settings = Settings()
