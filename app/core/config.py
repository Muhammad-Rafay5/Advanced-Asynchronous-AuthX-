from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Advanced Asynchronous Backend"
    ACCESS_TOKEN_SECRET: str
    REFRESH_TOKEN_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    CORS_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"
    BCRYPT_ROUNDS: int = 12

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
