from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Meeting Minute Chatbot"
    app_env: str = "development"

    # OpenAI
    openai_api_key: str

    # Groq 
    groq_api_key: str = "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"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "meeting_chatbot"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480

    # ChromaDB
    chroma_persist_path: str = "./storage/chroma"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = "/teamspace/studios/this_studio/meeting_minutes/.env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()