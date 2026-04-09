# color-restoration

Monorepo: **`backend/`** (FastAPI + TensorFlow), **`frontend/`** (Next.js), **`data/`** (veri setleri).

```text
color-restoration/
├── backend/
│   ├── app/
│   ├── Dockerfile
│   ├── train/
│   ├── scripts/
│   ├── tests/
│   ├── models/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   └── Dockerfile
├── docker-compose.yml
├── data/
└── README.md
```

## Backend kurulum

```bash
cd backend
python -m venv ..\.venv
..\.venv\Scripts\activate
pip install -e ".[dev]"
```

(İstersen `.venv` yalnızca `backend` içinde de oluşturabilirsin.)

PowerShell’de kurulum: `pip install -e '.\backend[dev]'` (köşeli parantez için tek tırnak).

Paket adı `color-restoration` olarak değiştiyse eski editable kurulumu kaldırıp yeniden kurun: `pip uninstall color-restoration-backend -y` (varsa), ardından yukarıdaki `pip install -e`.

### Yol kuralları (modüler monorepo)

| Ne | Göreli yol neye göre? |
|----|------------------------|
| `data/raw`, `data/processed`, `--train-dir` / `--val-dir` / dataset script argümanları | **Repo kökü** (`color-restoration/`) |
| `models/colorization.keras`, `CR_MODEL_PATH` (göreliyse) | **`backend/`** kökü |
| `uvicorn app.main:app` | Çalışma dizini **`backend`** olmalı |

Scriptler `__file__` ile repo / backend kökünü bulur; komutu nereden çalıştırdığın önemli değil.

## Dataset hazırlama

Görselleri repo kökünde `data/raw` altına koy. Aşağıdaki komutlar **herhangi bir dizinden** çalışır; göreli yollar repo köküne göre çözülür:

```bash
python backend/scripts/prepare_dataset.py ^
  --train-source-dir data/raw/DIV2K_train_HR ^
  --val-source-dir data/raw/DIV2K_valid_HR ^
  --target-dir data/processed ^
  --test-ratio 0.05
```

Tek klasör (legacy):

```bash
python backend/scripts/prepare_dataset.py --source-dir data/raw --target-dir data/processed --val-ratio 0.1 --test-ratio 0.05
```

## Model eğitimi

Varsayılanlar: train/val = `data/processed/...` (repo kökü), çıktı modeli = `backend/models/colorization.keras`.

```bash
python backend/train/train_baseline.py --epochs 15 --batch-size 16 --image-size 128 --learning-rate 3e-4
```

Özel klasörler için örnek:

```bash
python backend/train/train_baseline.py --train-dir data/processed/train --val-dir data/processed/val --output-model-path models/colorization.keras
```

(`--output-model-path` göreliyse `backend/` köküne göredir.)

## Ortam değişkenleri (API)

```bash
cd backend
copy .env.example .env
```

`CR_MODEL_PATH` varsayılan: `models/colorization.keras` (çalışma dizini **`backend`** olmalı).

## API’yi çalıştır

**Çalışma dizini `backend` olmalı** (`app` paketi burada çözülür):

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Windows:

```powershell
.\backend\scripts\run_backend.ps1
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Arayüz, proxy ile backend’e gider. Gerekirse `frontend/.env.local` içinde `COLOR_RESTORATION_API_URL=http://127.0.0.1:8000`.

## Docker (Compose)

Önkoşul: eğitilmiş model dosyası **`backend/models/colorization.keras`** yolunda olsun (volume bu klasörü konteynıra salt okunur bağlar).

```bash
docker compose build
docker compose up
```

- **Frontend:** http://localhost:3000  
- **API:** http://localhost:8000 — Swagger: http://localhost:8000/docs  

Compose içinde Next.js sunucusu, proxy için `COLOR_RESTORATION_API_URL=http://backend:8000` kullanır (Docker ağındaki servis adı).

Tek imaj derlemek için:

```bash
docker build -t color-restoration-api ./backend
docker build -t color-restoration-web ./frontend
```

**Notlar**

- Backend imajı ilk derlemede TensorFlow indirdiği için uzun sürebilir; healthcheck `start_period` buna göre ayarlıdır.
- Apple Silicon üzerinde TensorFlow için gerekiyorsa `docker-compose.yml` içinde `backend` servisine `platform: linux/amd64` ekleyebilirsin (emülasyon yavaş olabilir).

## Endpointler

- `GET /` — servis durumu
- `GET /api/v1/health`
- `POST /api/v1/images/colorize`

## Smoke test (inference)

```bash
cd backend
python scripts/smoke_test_inference.py
```

## Backend testleri

```bash
cd backend
pytest
```

## Notlar

- Eğitim ve inference ön-işleme aynı kalmalı (`KerasColorizationAdapter` ile `train_baseline` uyumu).
- Eski düzen: proje kökünde tek `app/` vardı; artık tüm Python tarafı **`backend/`** altında.
