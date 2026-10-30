from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://vortex:vortex@localhost:5432/vortexhealing"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    LM_STUDIO_URL: str = "http://localhost:1234/v1"
    QWEN_MODEL: str = "qwen/qwen3.8-27b"  # LM Studio identifier; a bare name makes it load a second copy
    QWEN_LOAD_KEY: str = "qwen/qwen3.8-27b@4bit"  # the MLX file, faster on Apple silicon than the GGUF one
    QWEN_CONTEXT: int = 32768
    EMBED_MODEL: str = "text-embedding-nomic-embed-text-v1.5"
    LMS_PATH: str = "~/.lmstudio/bin/lms"
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: str = "noreply@vortexhealing.com"
    FRONTEND_URL: str = "http://localhost:3000"
    HANDOUTS_DIR: Optional[str] = None
    HANDOUTS_KB_DIR: str = "~/Documents/Handouts-KB"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
