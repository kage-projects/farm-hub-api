from functools import lru_cache
from typing import List, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str 
    api_title: str = "FarmHub API"
    api_version: str = "1.0.0"
    
    cors_allowed_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allowed_methods: List[str] = ["*"]
    cors_allowed_headers: List[str] = ["*"]

    secret_key: str 
    algorithm: str = "HS256"
    access_token_expire_minutes: int 
    apikey_gemini: str
    bcrypt_rounds: int = 12 
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow" 

    @field_validator("cors_allowed_origins", mode="before")
    def _parse_cors_allowed_origins(cls, v: Any) -> List[str]:
        """Allow env to pass JSON array or comma-separated string."""
        # If already a list, return as-is
        if isinstance(v, (list, tuple)):
            return list(v)
        if v is None:
            return []
        # If string, try JSON first, then comma-split
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("[") and s.endswith("]"):
                try:
                    import json

                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x) for x in parsed]
                except Exception:
                    # fallthrough to comma-split
                    pass
            # comma-separated
            return [item.strip() for item in s.split(",") if item.strip()]
        # otherwise coerce to str
        return [str(v)]

@lru_cache()
def get_settings() -> Settings:
    return Settings()