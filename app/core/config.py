from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # OpenAI
    OPENAI_API_KEY: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "LMS для правоохранительной академии"

    # CORS
    CORS_ORIGINS: str = "*"  # Comma-separated list of allowed origins, e.g., "http://localhost:3000,https://example.com"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"  # Comma-separated list, e.g., "GET,POST,PUT,DELETE"
    CORS_ALLOW_HEADERS: str = "*"  # Comma-separated list

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def cors_methods_list(self) -> List[str]:
        """Convert CORS_ALLOW_METHODS string to list."""
        if self.CORS_ALLOW_METHODS == "*":
            return ["*"]
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",")]

    @property
    def cors_headers_list(self) -> List[str]:
        """Convert CORS_ALLOW_HEADERS string to list."""
        if self.CORS_ALLOW_HEADERS == "*":
            return ["*"]
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
