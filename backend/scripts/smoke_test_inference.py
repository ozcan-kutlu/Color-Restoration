from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from app.core.config import get_settings
from app.infrastructure.inference.keras_colorization_adapter import KerasColorizationAdapter

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    input_path = _BACKEND_ROOT / "scripts" / "sample_bw.png"
    output_path = _BACKEND_ROOT / "scripts" / "sample_colorized.png"

    image = Image.new("L", (128, 128), color=160).convert("RGB")
    input_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(input_path)

    adapter = KerasColorizationAdapter(settings=get_settings())
    with input_path.open("rb") as f:
        source_bytes = f.read()

    result = adapter.colorize(source_bytes)
    colorized = Image.open(BytesIO(result.image_bytes))
    colorized.save(output_path)

    print(f"Input : {input_path.as_posix()}")
    print(f"Output: {output_path.as_posix()}")


if __name__ == "__main__":
    main()
