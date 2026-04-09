"""Konteyner ayağa kalkarken: model zaten imajda / volume'da varsa geç; yoksa CR_MODEL_DOWNLOAD_URL'den indir."""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path


def resolved_path() -> Path:
    raw = os.environ.get("CR_MODEL_PATH", "models/colorization.keras").strip()
    p = Path(raw)
    if p.is_absolute():
        return p
    return Path("/app") / p


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
            "  • Render: Environment Variables → CR_MODEL_DOWNLOAD_URL = .keras dosyasına "
            "doğrudan HTTPS linki (ör. GitHub Releases 'assets' raw, S3/R2 public URL).\n"
            "  • Yerel Docker: backend/models/colorization.keras dosyasını oluşturun veya aynı env'i verin.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Model indiriliyor → {path}")
    tmp = path.with_suffix(path.suffix + ".partial")
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
        tmp.replace(path)
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

    print(f"Model indirildi: {path} ({path.stat().st_size} byte)")


if __name__ == "__main__":
    main()
