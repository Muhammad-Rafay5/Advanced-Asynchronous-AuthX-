from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Advanced Asynchronous Backend"
    ACCESS_TOKEN_SECRET: str = "super_secret_access_key_12345"
    REFRESH_TOKEN_SECRET: str = "even_more_secret_refresh_key_67890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite+aiosqlite:///./auth_system.db"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"

settings = Settings()
