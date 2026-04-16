from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    OPENAI_API_KEY: str
    ENCRYPTION_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
