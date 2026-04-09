# Color Restoration

Siyah-beyaz veya soluk görselleri renklendirmek için bir uygulama: **Next.js** arayüzü ve **FastAPI + TensorFlow (Keras)** ile çalışan bir API. Monorepo yapısında `backend/`, `frontend/` ve isteğe bağlı `data/` klasörleri bulunur.

---

## Özellikler

- Web arayüzünden görsel yükleme ve renklendirme sonucunu görüntüleme
- REST API (`/api/v1/images/colorize`) ve Swagger dokümantasyonu (`/docs`)
- Docker Compose ile tek komutta backend + frontend çalıştırma
- Yerel geliştirme için ayrı backend ve frontend sunucuları
- `render.yaml` ve `frontend/vercel.json` ile Render / Vercel yayınına uyum

---

## Gereksinimler

| Ne zaman | Gerekli olanlar |
|----------|-----------------|
| **Docker ile çalıştırma** | [Docker](https://docs.docker.com/get-docker/) + eğitilmiş model dosyası (`backend/models/colorization.keras`) |
| **Yerel geliştirme** | Python 3.10+ (önerilir), Node.js 20+, `npm` |

---

## En hızlı başlangıç (Docker)

1. Eğitilmiş modeli şu konuma koy: **`backend/models/colorization.keras`**
2. Proje kökünde:

```bash
docker compose build
docker compose up
```

3. Tarayıcıda aç:
   - **Uygulama:** http://localhost:3000  
   - **API:** http://localhost:8000  
   - **API dokümantasyonu:** http://localhost:8000/docs  

İlk backend derlemesi TensorFlow indireceği için uzun sürebilir. Apple Silicon’da sorun olursa `docker-compose.yml` içinde backend servisine `platform: linux/amd64` eklemeyi deneyebilirsin (daha yavaş olabilir).

---

## Yerel geliştirme

### 1. Backend (API)

```bash
cd backend
python -m venv ..\.venv
..\.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

PowerShell (repo kökünden, köşeli parantez için tek tırnak):

```powershell
pip install -e '.\backend[dev]'
```

Windows’ta kısayol: `.\backend\scripts\run_backend.ps1`

**Önemli:** `uvicorn` komutunu çalıştırırken çalışma dizini **`backend`** olmalı. Model yolu varsayılan olarak `models/colorization.keras` (yine `backend` köküne göre).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Arayüz genelde http://localhost:3000 adresinde açılır. Backend farklı bir adresteyse `frontend/.env.local` içinde:

```env
COLOR_RESTORATION_API_URL=http://127.0.0.1:8000
```

---

## Proje yapısı

```text
color-restoration/
├── backend/          # FastAPI, eğitim scriptleri, testler, models/
├── frontend/         # Next.js uygulaması
├── data/             # Ham/işlenmiş veri setleri (.gitignore ile büyük dosyalar hariç)
├── docker-compose.yml
└── README.md
```

---

## Veri seti ve model eğitimi

Görselleri repo kökünde **`data/raw`** altına koy. Aşağıdaki komutlar hangi dizinden çalıştırılırsa çalıştırılsın göreli yollar repo köküne göre çözülür.

**Veri hazırlama (örnek):**

```bash
python backend/scripts/prepare_dataset.py ^
  --train-source-dir data/raw/DIV2K_train_HR ^
  --val-source-dir data/raw/DIV2K_valid_HR ^
  --target-dir data/processed ^
  --test-ratio 0.05
```

Tek kaynak klasör:

```bash
python backend/scripts/prepare_dataset.py --source-dir data/raw --target-dir data/processed --val-ratio 0.1 --test-ratio 0.05
```

**Eğitim (varsayılan çıktı: `backend/models/colorization.keras`):**

```bash
python backend/train/train_baseline.py --epochs 15 --batch-size 16 --image-size 128 --learning-rate 3e-4
```

Özel klasörler:

```bash
python backend/train/train_baseline.py --train-dir data/processed/train --val-dir data/processed/val --output-model-path models/colorization.keras
```

(`--output-model-path` göreliyse **`backend/`** köküne göredir.)

---

## Ortam değişkenleri (backend)

`backend/.env.example` dosyasını `.env` olarak kopyala. Özet:

| Değişken | Açıklama |
|----------|----------|
| `CR_MODEL_PATH` | Keras model dosyası (varsayılan: `models/colorization.keras`) |
| `CR_INFERENCE_IMAGE_SIZE` | Çıkarım için görüntü boyutu |
| `CR_ENVIRONMENT` | Örn. `dev` / `prod` |
| `CR_CORS_ORIGINS` | İsteğe bağlı; virgülle ayrılmış `https://...` listesi (boşsa CORS middleware yok) |

---

## API uç noktaları

| Metod | Yol | Açıklama |
|--------|-----|----------|
| `GET` | `/` | Servis durumu |
| `GET` | `/api/v1/health` | Sağlık kontrolü |
| `POST` | `/api/v1/images/colorize` | Görsel renklendirme |

---

## Test ve doğrulama

```bash
cd backend
pytest
```

Çıkarım duman testi:

```bash
cd backend
python scripts/smoke_test_inference.py
```

---

## Yol kuralları (kısa özet)

| Konu | Göreli yol neye göre? |
|------|------------------------|
| `data/raw`, `data/processed`, dataset script argümanları | **Repo kökü** |
| `models/colorization.keras`, `CR_MODEL_PATH` (göreliyse) | **`backend/`** kökü |
| `uvicorn app.main:app` | Çalışma dizini **`backend`** |

Scriptler repo/backend kökünü `__file__` ile bulduğu için birçok komut farklı dizinden de çalışır; API için çalışma dizini kuralına dikkat et.

---

## Docker (tek imaj)

```bash
docker build -t color-restoration-api ./backend
docker build -t color-restoration-web ./frontend
```

Compose içinde frontend, ağ üzerinden `COLOR_RESTORATION_API_URL=http://backend:8000` kullanır.

---

## Yayınlama (Render + Vercel)

### Akış

1. **Render:** API’yi deploy et, public URL’i not al (örn. `https://color-restoration-api.onrender.com`).
2. **Vercel:** GitHub repo’sunu import et; **Root Directory** olarak `frontend` seç.
3. **Vercel → Settings → Environment Variables:** `COLOR_RESTORATION_API_URL` = Render’daki API tabanı (**sonda `/` olmadan**). Production (ve gerekirse Preview) için tanımla.
4. **İsteğe bağlı — CORS:** Arayüz sunucu üzerinden `/api/colorize` ile proxy yaptığı için tarayıcı doğrudan Render’a gitmez; yine de Swagger veya başka bir origin’den API’ye erişeceksen Render’da `CR_CORS_ORIGINS` ekle (örn. `https://proje-adin.vercel.app`).

### Render (backend)

- Repo kökündeki [`render.yaml`](render.yaml) ile [Blueprint](https://render.com/docs/blueprint-spec) oluşturabilir veya manuel **Web Service → Docker** ekleyebilirsin: **Dockerfile** `backend/Dockerfile`, **Docker build context** `backend`.
- **Sağlık kontrolü yolu:** `/api/v1/health`
- **Plan:** `render.yaml` içinde `plan: free` (ücretsiz; uyku ve aylık saat limiti vardır). Ücretli planda [Persistent Disk](https://render.com/docs/disks) ile model saklanabilir; **free’de disk yok** — modeli imaja dahil etmek (`.dockerignore`’da `models/*.keras` kuralını kaldırıp build’e dosyayı eklemek) veya deploy sırasında güvenilir bir URL’den indirmek gerekir.
- Platform **`PORT`** ortam değişkenini verir; Docker imajı buna uyumludur.

### Vercel (frontend)

- Proje dizini **`frontend/`** olmalı; kökteki `vercel.json` Next.js için `app/api/colorize/route.ts` rotasına **`maxDuration`: 60** saniye verir (Vercel planına göre üst sınır farklı olabilir; ağır isteklerde Pro veya daha yüksek limit gerekebilir).
- Örnek ortam değişkeni: `frontend/.env.example`.

---

## Sorun giderme

- **Backend “modül bulunamadı”:** Komutu `backend` klasöründen çalıştırdığından emin ol.
- **Eski editable kurulum:** Paket adı değiştiyse `pip uninstall color-restoration-backend -y` (varsa), sonra `backend` içinde `pip install -e ".[dev]"` ile yeniden kur.

## Notlar

- Eğitim ve çıkarım ön-işlemesi uyumlu kalmalı (`train_baseline` ↔ `KerasColorizationAdapter`).
- Büyük veri ve ağırlık dosyaları `.gitignore` ile repodan hariç tutulur; modeli kendin üret veya sağla.
