from dataclasses import dataclass


@dataclass(slots=True)
class ColorizationResult:
    image_bytes: bytes
    content_type: str = "image/png"
