from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _resolve_path(path_str: str) -> Path:
    p = Path(path_str)
    return p.resolve() if p.is_absolute() else (_REPO_ROOT / p).resolve()


def gather_images(source_dir: Path) -> list[Path]:
    image_paths: list[Path] = []
    for path in source_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            image_paths.append(path)
    return image_paths


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def split_counts(total: int, val_ratio: float, test_ratio: float) -> tuple[int, int, int]:
    val_count = int(total * val_ratio)
    test_count = int(total * test_ratio)
    train_count = total - val_count - test_count
    return train_count, val_count, test_count


def copy_split(images: list[Path], target_dir: Path, split_name: str) -> None:
    split_dir = target_dir / split_name
    split_dir.mkdir(parents=True, exist_ok=True)

    for idx, src in enumerate(images):
        suffix = src.suffix.lower()
        dst = split_dir / f"{split_name}_{idx:07d}{suffix}"
        shutil.copy2(src, dst)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare train/val/test folders from raw images",
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default="data/raw",
        help="Single folder: shuffle all images and split train/val/test (legacy).",
    )
    parser.add_argument(
        "--train-source-dir",
        type=str,
        default=None,
        help="Official train set (e.g. DIV2K_train_HR): split into train + test only.",
    )
    parser.add_argument(
        "--val-source-dir",
        type=str,
        default=None,
        help="Official validation set (e.g. DIV2K_valid_HR): all images go to val/.",
    )
    parser.add_argument("--target-dir", type=str, default="data/processed")
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.1,
        help="Legacy single-source mode only: fraction for val.",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.05,
        help="Legacy: fraction for test. Two-source mode: fraction of train set for test.",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_dir = _resolve_path(args.target_dir)
    use_two_source = args.train_source_dir is not None and args.val_source_dir is not None

    if use_two_source:
        train_source = _resolve_path(args.train_source_dir)
        val_source = _resolve_path(args.val_source_dir)

        if not train_source.exists():
            raise FileNotFoundError(f"Train source not found: {train_source.as_posix()}")
        if not val_source.exists():
            raise FileNotFoundError(f"Val source not found: {val_source.as_posix()}")
        if args.test_ratio < 0 or args.test_ratio >= 1:
            raise ValueError("test-ratio must be >= 0 and < 1 in two-source mode.")

        train_pool = gather_images(train_source)
        val_images = gather_images(val_source)

        if not train_pool:
            raise ValueError(f"No images in train source: {train_source.as_posix()}")
        if not val_images:
            raise ValueError(f"No images in val source: {val_source.as_posix()}")

        random.seed(args.seed)
        random.shuffle(train_pool)

        n_test = int(len(train_pool) * args.test_ratio)
        test_images = train_pool[:n_test]
        train_images = train_pool[n_test:]

        ensure_clean_dir(target_dir / "train")
        ensure_clean_dir(target_dir / "val")
        ensure_clean_dir(target_dir / "test")

        copy_split(train_images, target_dir, "train")
        copy_split(val_images, target_dir, "val")
        copy_split(test_images, target_dir, "test")

        print("Dataset prepared successfully (official train / val split preserved).")
        print(f"Train source images : {len(train_pool)} -> train {len(train_images)}, test {len(test_images)}")
        print(f"Val source images   : {len(val_images)} -> val (all)")
        print(f"Target: {target_dir.as_posix()}")
        return

    if args.train_source_dir is not None or args.val_source_dir is not None:
        raise ValueError(
            "Provide both --train-source-dir and --val-source-dir, or use single --source-dir only."
        )

    source_dir = _resolve_path(args.source_dir)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir.as_posix()}")
    if args.val_ratio < 0 or args.test_ratio < 0 or (args.val_ratio + args.test_ratio) >= 1:
        raise ValueError("val-ratio and test-ratio must be >=0 and sum must be <1.")

    images = gather_images(source_dir)
    if not images:
        raise ValueError(f"No supported images found in {source_dir.as_posix()}")

    random.seed(args.seed)
    random.shuffle(images)

    train_count, val_count, test_count = split_counts(
        total=len(images),
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
    )

    train_images = images[:train_count]
    val_images = images[train_count : train_count + val_count]
    test_images = images[train_count + val_count :]

    ensure_clean_dir(target_dir / "train")
    ensure_clean_dir(target_dir / "val")
    ensure_clean_dir(target_dir / "test")

    copy_split(train_images, target_dir, "train")
    copy_split(val_images, target_dir, "val")
    copy_split(test_images, target_dir, "test")

    print("Dataset prepared successfully (single-source shuffle split).")
    print(f"Total : {len(images)}")
    print(f"Train : {len(train_images)}")
    print(f"Val   : {len(val_images)}")
    print(f"Test  : {len(test_images)}")
    print(f"Target: {target_dir.as_posix()}")


if __name__ == "__main__":
    main()
