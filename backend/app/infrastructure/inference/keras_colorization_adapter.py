from io import BytesIO

import numpy as np
from PIL import Image
from tensorflow import keras

from app.core.config import Settings
from app.domain.entities.colorization_result import ColorizationResult
from app.domain.interfaces import ColorizationModelPort


class KerasColorizationAdapter(ColorizationModelPort):
    """
    Adapter for TensorFlow/Keras model inference.

    Note:
    - This is a production-ready skeleton with a clear contract.
    - The preprocessing/postprocessing pipeline should be aligned with the
      custom training pipeline your team will implement.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = keras.models.load_model(settings.model_path)
        self._input_size = self._resolve_input_size()

    def _resolve_input_size(self) -> int:
        shape = self._model.input_shape
        if isinstance(shape, list):
            shape = shape[0]

        if len(shape) == 4 and shape[1] and shape[2]:
            return int(shape[1])
        return self._settings.inference_image_size

    def colorize(self, image_bytes: bytes) -> ColorizationResult:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        original_size = image.size

        # The baseline model is trained with grayscale replicated into 3 channels.
        grayscale = image.convert("L").convert("RGB")
        resized = grayscale.resize(
            (self._input_size, self._input_size),
            resample=Image.Resampling.LANCZOS,
        )
        x = np.asarray(resized, dtype=np.float32) / 255.0
        x = np.expand_dims(x, axis=0)

        prediction = self._model.predict(x, verbose=0)[0]
        prediction = np.clip(prediction, 0.0, 1.0)
        output = (prediction * 255).astype(np.uint8)

        output_image = Image.fromarray(output).resize(
            original_size,
            resample=Image.Resampling.LANCZOS,
        )
        buffer = BytesIO()
        output_image.save(buffer, format="PNG")
        return ColorizationResult(image_bytes=buffer.getvalue(), content_type="image/png")
