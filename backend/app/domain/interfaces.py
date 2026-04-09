from abc import ABC, abstractmethod

from app.domain.entities.colorization_result import ColorizationResult


class ColorizationModelPort(ABC):
    @abstractmethod
    def colorize(self, image_bytes: bytes) -> ColorizationResult:
        """Return colorized image bytes from raw uploaded image."""
