# ══════════════════════════════════════════════════════════════
# ai_service/config.py
# ══════════════════════════════════════════════════════════════
from pydantic_settings import BaseSettings
from typing import List
 
 
class Settings(BaseSettings):
    openai_api_key:   str = ""
    openai_model:     str = "gpt-4"
    mongodb_uri:      str = "mongodb://mediconnect_user:mediconnect_dev_password@localhost:27017/mediconnect?authSource=admin"
    redis_url:        str = "redis://localhost:6379/2"
    backend_base_url: str = "http://backend-service:8000"
    cors_origins:     List[str] = ["https://mediconnect.salman-aak.com", "http://localhost:5173"]
    log_level:        str = "INFO"
    model_path:       str = "/app/models"
 
    class Config:
        env_file = ".env"
        case_sensitive = False
 
 
settings = Settings()
 
