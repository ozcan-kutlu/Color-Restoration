from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field

from app.core.paths import backend_root


def _resolve_model_path(raw: str) -> str:
    """Göreli yolları `backend/`e göre çöz; çalışma dizininden bağımsız."""
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    return str((backend_root() / p).resolve())


class Settings(BaseModel):
    app_name: str = "color-restoration"
    api_v1_prefix: str = "/api/v1"
    environment: str = "dev"
    model_path: str = Field(default="models/colorization.keras")
    inference_image_size: int = Field(default=256, ge=64, le=1024)


@lru_cache
def get_settings() -> Settings:
    raw_model = os.getenv("CR_MODEL_PATH", "models/colorization.keras")
    return Settings(
        app_name=os.getenv("CR_APP_NAME", "color-restoration"),
        api_v1_prefix=os.getenv("CR_API_V1_PREFIX", "/api/v1"),
        environment=os.getenv("CR_ENVIRONMENT", "dev"),
        model_path=_resolve_model_path(raw_model),
        inference_image_size=int(os.getenv("CR_INFERENCE_IMAGE_SIZE", "256")),
    )
