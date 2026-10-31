import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

def _load_env_file(filepath: Path) -> None:
    """Manually parse .env file to populate os.environ without external dependencies."""
    if not filepath.exists():
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

# Determine project base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_load_env_file(BASE_DIR / ".env")

class Settings(BaseModel):
    APP_NAME: str = "PolitiTrade LK"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8001"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/politi_trade.db")
    
    BASE_DIR: Path = BASE_DIR
    STOCK_DATASET_DIR: Path = BASE_DIR / os.getenv("STOCK_DATASET_DIR", "Dataset-Stock")
    EVENT_DATASET_DIR: Path = BASE_DIR / os.getenv("EVENT_DATASET_DIR", "Dataset-Events")
    ARTIFACT_DIR: Path = BASE_DIR / os.getenv("ARTIFACT_DIR", "artifacts")
    DATA_PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    
    NEWS_API_KEY: Optional[str] = os.getenv("NEWS_API_KEY", "")
    NEWS_POLL_MINUTES: int = int(os.getenv("NEWS_POLL_MINUTES", "15"))
    
    LIVE_PROVIDER: str = os.getenv("LIVE_PROVIDER", "cse_unofficial")
    LIVE_CACHE_SECONDS: int = int(os.getenv("LIVE_CACHE_SECONDS", "30"))
    
    MODEL_RANDOM_STATE: int = int(os.getenv("MODEL_RANDOM_STATE", "42"))

settings = Settings()
