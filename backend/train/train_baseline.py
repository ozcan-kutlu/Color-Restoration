from __future__ import annotations

import argparse
from pathlib import Path

import tensorflow as tf
from tensorflow import keras

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _resolve_path(arg: str, *, base: Path) -> Path:
    p = Path(arg)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def conv_block(x: tf.Tensor, filters: int) -> tf.Tensor:
    x = keras.layers.Conv2D(filters, 3, padding="same")(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.ReLU()(x)
    x = keras.layers.Conv2D(filters, 3, padding="same")(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.ReLU()(x)
    return x


def build_unet_model(image_size: int, learning_rate: float) -> keras.Model:
    inputs = keras.Input(shape=(image_size, image_size, 3), name="grayscale_input")

    e1 = conv_block(inputs, 64)
    p1 = keras.layers.MaxPool2D(pool_size=2)(e1)

    e2 = conv_block(p1, 128)
    p2 = keras.layers.MaxPool2D(pool_size=2)(e2)

    e3 = conv_block(p2, 256)
    p3 = keras.layers.MaxPool2D(pool_size=2)(e3)

    b = conv_block(p3, 512)

    u3 = keras.layers.UpSampling2D(size=2, interpolation="bilinear")(b)
    u3 = keras.layers.Concatenate()([u3, e3])
    d3 = conv_block(u3, 256)

    u2 = keras.layers.UpSampling2D(size=2, interpolation="bilinear")(d3)
    u2 = keras.layers.Concatenate()([u2, e2])
    d2 = conv_block(u2, 128)

    u1 = keras.layers.UpSampling2D(size=2, interpolation="bilinear")(d2)
    u1 = keras.layers.Concatenate()([u1, e1])
    d1 = conv_block(u1, 64)

    outputs = keras.layers.Conv2D(3, 1, padding="same", activation="sigmoid", name="rgb_output")(d1)

    model = keras.Model(inputs=inputs, outputs=outputs, name="unet_colorization_model")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="mae",
        metrics=[keras.metrics.MeanSquaredError(name="mse")],
    )
    return model


def _decode_and_resize(image_path: tf.Tensor, image_size: int) -> tf.Tensor:
    image_bytes = tf.io.read_file(image_path)
    image = tf.io.decode_image(image_bytes, channels=3, expand_animations=False)
    image = tf.image.resize(image, (image_size, image_size))
    image = tf.cast(image, tf.float32) / 255.0
    return image


def _to_gray_input(color_image: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
    gray = tf.image.rgb_to_grayscale(color_image)
    gray_rgb = tf.repeat(gray, repeats=3, axis=-1)
    return gray_rgb, color_image


def build_dataset_from_dir(
    directory: str, image_size: int, batch_size: int, shuffle: bool
) -> tf.data.Dataset:
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    image_paths: list[str] = []
    for ext in exts:
        image_paths.extend(str(p) for p in Path(directory).rglob(ext))
        image_paths.extend(str(p) for p in Path(directory).rglob(ext.upper()))

    if not image_paths:
        raise ValueError(f"No image files found in: {directory}")

    ds = tf.data.Dataset.from_tensor_slices(image_paths)
    if shuffle:
        ds = ds.shuffle(buffer_size=min(len(image_paths), 10000), reshuffle_each_iteration=True)

    ds = ds.map(lambda p: _decode_and_resize(p, image_size), num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.map(_to_gray_input, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds


def train(args: argparse.Namespace) -> None:
    if args.mixed_precision:
        try:
            keras.mixed_precision.set_global_policy("mixed_float16")
            print("Mixed precision enabled: mixed_float16")
        except Exception as exc:
            print(f"Mixed precision unavailable, fallback to float32: {exc}")

    train_dir = _resolve_path(args.train_dir, base=_REPO_ROOT)
    val_dir = _resolve_path(args.val_dir, base=_REPO_ROOT)

    train_ds = build_dataset_from_dir(
        directory=str(train_dir),
        image_size=args.image_size,
        batch_size=args.batch_size,
        shuffle=True,
    )
    val_ds = build_dataset_from_dir(
        directory=str(val_dir),
        image_size=args.image_size,
        batch_size=args.batch_size,
        shuffle=False,
    )

    model = build_unet_model(args.image_size, args.learning_rate)
    model.summary()

    callbacks: list[keras.callbacks.Callback] = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2),
    ]

    model.fit(
        x=train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=callbacks,
        verbose=1,
    )

    output_path = _resolve_path(args.output_model_path, base=_BACKEND_ROOT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(output_path)
    print(f"Saved model: {output_path.as_posix()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train U-Net Keras colorization model")
    parser.add_argument(
        "--train-dir",
        type=str,
        default=str(_REPO_ROOT / "data" / "processed" / "train"),
        help="Eğitim görselleri (göreli yol repo köküne göredir).",
    )
    parser.add_argument(
        "--val-dir",
        type=str,
        default=str(_REPO_ROOT / "data" / "processed" / "val"),
        help="Doğrulama görselleri (göreli yol repo köküne göredir).",
    )
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Yüksek çözünürlük için varsayılan batch-size düşürüldü (VRAM/RAM dostu).",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=256,
        help="Eğitim giriş çözünürlüğü (öneri: 256+, bellek yeterliyse 384/512).",
    )
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument(
        "--mixed-precision",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="GPU'da eğitim hız/bellek verimi için mixed precision kullan.",
    )
    parser.add_argument(
        "--output-model-path",
        type=str,
        default=str(_BACKEND_ROOT / "models" / "colorization.keras"),
        help="Çıktı modeli (göreli yol repo köküne göre değil, backend/ köküne göre).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    tf.random.set_seed(42)
    train(parse_args())
