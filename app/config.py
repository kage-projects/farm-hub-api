from functools import lru_cache
from typing import List, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    database_url: str 
    api_title: str = "FarmHub API"
    api_version: str = "1.0.0"

    secret_key: str 
    algorithm: str = "HS256"
    access_token_expire_minutes: int 
    apikey_gemini: str
    bcrypt_rounds: int = 12 
    qdrant_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow" 


@lru_cache()
def get_settings() -> Settings:
    return Settings()