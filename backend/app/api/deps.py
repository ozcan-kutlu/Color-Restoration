from functools import lru_cache

from app.application.services.colorize_service import ColorizeImageService
from app.core.config import Settings, get_settings


@lru_cache
def get_model_adapter():
    from app.infrastructure.inference.keras_colorization_adapter import (
        KerasColorizationAdapter,
    )

    settings: Settings = get_settings()
    return KerasColorizationAdapter(settings=settings)


def get_colorize_service() -> ColorizeImageService:
    adapter = get_model_adapter()
    return ColorizeImageService(model_port=adapter)
