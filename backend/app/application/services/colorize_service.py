from app.domain.entities.colorization_result import ColorizationResult
from app.domain.interfaces import ColorizationModelPort


class ColorizeImageService:
    def __init__(self, model_port: ColorizationModelPort) -> None:
        self._model_port = model_port

    def execute(self, image_bytes: bytes) -> ColorizationResult:
        return self._model_port.colorize(image_bytes)
