# OrbitGuard Kurulum ve Çalıştırma Rehberi

## Hızlı Başlangıç

### Windows
```bash
run.bat
```

### Linux/macOS
```bash
chmod +x run.sh
./run.sh
```

## Kurulum Adımları

### 1. Python Bağımlılıklarını Yükle
```bash
pip install -r requirements.txt
```

### 2. Kurulum Kontrolü
```bash
python check_setup.py
```

Bu komut şunları kontrol eder:
- ✓ Tüm Python bağımlılıkları
- ✓ Gerekli dosyalar
- ✓ Port kullanılabilirliği (8000, 8001)

## Sorun Giderme

### Sorun: Backend/Kamera penceresi hemen kapanıyor

**Çözüm 1: Bağımlılıkları kontrol et**
```bash
python check_setup.py
```

Eksik bağımlılıklar varsa:
```bash
pip install -r requirements.txt
```

**Çözüm 2: Hataları görmek için manuel başlat**

Terminal 1 - Backend:
```bash
python main.py
```

Terminal 2 - Kamera Servisi:
```bash
python camera_service.py
```

Terminal 3 - Frontend:
```bash
# Tarayıcıda aç: http://127.0.0.1:8000
```

### Sorun: "Port already in use" hatası

**Çözüm: Diğer uygulamaları kapat**

Windows:
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

Linux/macOS:
```bash
lsof -i :8000
kill -9 <PID>
```

### Sorun: "ModuleNotFoundError" hatası

**Çözüm: Bağımlılıkları yeniden yükle**
```bash
pip install --upgrade -r requirements.txt
```

### Sorun: Webcam açılmıyor

**Çözüm: OpenCV ve webcam izinlerini kontrol et**

Windows:
- Kamera Uygulaması'nı kapatın
- Başka bir uygulama webcam kullanmıyor mu kontrol edin

Linux:
```bash
ls -la /dev/video0
```

macOS:
- Sistem Tercihleri → Güvenlik ve Gizlilik → Kamera → Python'a izin ver

## Servis Portları

| Servis | Port | URL |
|--------|------|-----|
| Backend API | 8000 | http://127.0.0.1:8000 |
| Kamera Servisi | 8001 | http://127.0.0.1:8001 |
| Frontend | 8000 | http://127.0.0.1:8000 |

## Dosya Yapısı

```
OrbitGuard/
├── main.py                 # Backend API
├── camera_service.py       # Kamera Servisi
├── middleware.py           # IP Erişim Kontrolü
├── dependencies.py         # Paylaşılan Bağımlılıklar
├── celestrak_client.py     # CelesTrak İstemcisi
├── sgp4_engine.py          # SGP4 Konum Hesaplama
├── conjunction.py          # Konjunksiyon Analizi
├── routers/                # API Router'ları
│   ├── search.py
│   ├── satellite.py
│   ├── groups.py
│   └── conjunction.py
├── frontend/
│   └── index.html          # Web Arayüzü
├── tests/                  # Test Dosyaları
├── requirements.txt        # Python Bağımlılıkları
├── run.bat                 # Windows Başlatma
├── run.sh                  # Linux/macOS Başlatma
└── check_setup.py          # Kurulum Kontrol

```

## API Endpoint'leri

### Backend (Port 8000)

- `GET /` - Frontend HTML
- `GET /health` - Sağlık Kontrolü
- `GET /api/search/name?q=<sorgu>` - İsim Araması
- `GET /api/search/catnr?id=<norad_id>` - NORAD_ID Araması
- `GET /api/satellite/{catnr}` - Uydu Bilgisi
- `GET /api/satellite/{catnr}/position` - Uydu Konumu
- `GET /api/satellite/{catnr}/orbital` - Yörünge Parametreleri
- `GET /api/groups/{group}` - Grup TLE Listesi
- `GET /api/groups/{group}/count` - Grup Sayısı
- `GET /api/conjunction/turkish-satellites` - Türk Uyduları Konjunksiyon
- `GET /api/conjunction/pair?sat1=<id1>&sat2=<id2>&days=7` - Çift Konjunksiyon
- `GET /api/camera/status` - Kamera Durumu (Proxy)

### Kamera Servisi (Port 8001)

- `POST /camera/start` - Kamerayı Başlat
- `POST /camera/stop` - Kamerayı Durdur
- `GET /camera/stream` - MJPEG Akışı
- `GET /camera/status` - Kamera Durumu
- `GET /camera/detections` - Algılanan Nesneler

## Test Çalıştırma

```bash
# Tüm testleri çalıştır
pytest tests/ -v

# Belirli bir test dosyasını çalıştır
pytest tests/test_middleware.py -v

# Özellik testlerini çalıştır (Hypothesis)
pytest tests/ -v -k "property"
```

## Geliştirme

### Yeni Router Ekleme

1. `routers/` dizininde yeni dosya oluştur
2. `FastAPI.APIRouter` kullan
3. `main.py`'de `app.include_router()` ile dahil et

### Yeni Test Ekleme

1. `tests/` dizininde `test_*.py` dosyası oluştur
2. Hypothesis ile özellik testleri yaz
3. `pytest tests/test_*.py -v` ile çalıştır

## Lisans

OrbitGuard — Türk Uydu Takip Sistemi
