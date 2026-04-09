"""Monorepo dizin sabitleri: `backend/` ve repo kökü."""

from pathlib import Path


def backend_root() -> Path:
    """`backend/` — `app/`, `train/`, `models/`, `pyproject.toml` burada."""
    return Path(__file__).resolve().parents[2]


def monorepo_root() -> Path:
    """Repo kökü (`backend/`in bir üstü). `data/` genelde burada."""
    return backend_root().parent
