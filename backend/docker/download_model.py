"""Konteyner ayağa kalkarken: model zaten imajda / volume'da varsa geç; yoksa CR_MODEL_DOWNLOAD_URL'den indir."""

from __future__ import annotations

import os
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


def resolved_path() -> Path:
    raw = os.environ.get("CR_MODEL_PATH", "models/colorization.keras").strip()
    p = Path(raw)
    if p.is_absolute():
        return p
    return Path("/app") / p


def _url_means_zip_archive(url: str) -> bool:
    path = urllib.parse.urlparse(url).path.lower().rstrip("/")
    return path.endswith(".zip")


def _force_zip_from_env() -> bool:
    v = os.getenv("CR_MODEL_DOWNLOAD_AS_ZIP", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _extract_keras_from_zip(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [m for m in zf.namelist() if not m.endswith("/")]
        model_members = [m for m in members if m.lower().endswith((".keras", ".h5"))]
        if not model_members:
            print(
                "ZIP içinde .keras veya .h5 yok. Örnek: colorization.zip içinde colorization.keras.",
                file=sys.stderr,
            )
            sys.exit(1)
        want_name = dest.name
        chosen: str | None = None
        for m in model_members:
            if Path(m).name == want_name:
                chosen = m
                break
        if chosen is None:
            chosen = model_members[0]
        data = zf.read(chosen)
    dest.write_bytes(data)


def main() -> None:
    path = resolved_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.is_file() and path.stat().st_size > 0:
        print(f"Model hazır: {path} ({path.stat().st_size} byte)")
        return

    url = os.environ.get("CR_MODEL_DOWNLOAD_URL", "").strip()
    if not url:
        print(
            "HATA: Model dosyası bulunamadı ve CR_MODEL_DOWNLOAD_URL tanımlı değil.\n"
            "  • Render: Environment → CR_MODEL_DOWNLOAD_URL\n"
            "    - Doğrudan .keras HTTPS linki, veya\n"
            "    - GitHub Release’ta .zip asset (içinde .keras) — URL .zip ile bitsin veya "
            "CR_MODEL_DOWNLOAD_AS_ZIP=1 kullanın.\n"
            "  • Yerel Docker: backend/models/colorization.keras oluşturun veya aynı env'i verin.",
            file=sys.stderr,
        )
        sys.exit(1)

    want_zip = _url_means_zip_archive(url) or _force_zip_from_env()
    tmp = path.parent / (path.name + ".partial")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "color-restoration-docker/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            with tmp.open("wb") as out:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
    except OSError as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        print(f"Model yazılamadı (klasör salt okunur olabilir): {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        print(f"İndirme başarısız: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if want_zip:
            if not zipfile.is_zipfile(tmp):
                print(
                    "Beklenen ZIP arşivi değil. URL .zip ile bitmeli veya dosya geçerli ZIP olmalı.",
                    file=sys.stderr,
                )
                sys.exit(1)
            _extract_keras_from_zip(tmp, path)
            tmp.unlink(missing_ok=True)
            print(f"Model ZIP’ten çıkarıldı: {path} ({path.stat().st_size} byte)")
        else:
            tmp.replace(path)
            print(f"Model indirildi: {path} ({path.stat().st_size} byte)")
    except SystemExit:
        raise
    except Exception as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        if path.exists():
            path.unlink(missing_ok=True)
        print(f"Model işlenemedi: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
