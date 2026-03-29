# OrbitGuard Sorun Çözümleri

## Sorun: Backend ve Frontend kapanıyor, sadece kamera açılıyor

### Kök Nedenleri

1. **Windows `run.bat` hataları göstermiyordu**
   - `start` komutu hataları gizliyordu
   - Pencereler hemen kapanıyordu

2. **Frontend sunulmuyordu**
   - Backend'de frontend dosyası serve edilmiyordu
   - Tarayıcı açılamıyordu

3. **Kurulum sorunları tespit edilemiyordu**
   - Bağımlılık eksikliği anlaşılmıyordu
   - Port çakışmaları kontrol edilmiyordu

## Yapılan Düzeltmeler

### 1. `run.bat` İyileştirildi

**Önceki:**
```batch
start "OrbitGuard Backend" python main.py
```

**Sonraki:**
```batch
start "OrbitGuard Backend" cmd /k "python main.py"
```

**Faydalar:**
- ✓ Hata mesajları görünüyor
- ✓ Pencere açık kalıyor
- ✓ Kurulum kontrol yapılıyor
- ✓ Frontend otomatik açılıyor

### 2. `main.py` Frontend Sunumu Eklendi

**Eklenen Kod:**
```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Frontend dosyasını serve et
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")

@app.get("/")
async def root():
    frontend_file = Path(__file__).parent / "frontend" / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file, media_type="text/html")
    return {"status": "ok", "version": "1.0"}
```

**Faydalar:**
- ✓ Frontend `http://127.0.0.1:8000` adresinden sunuluyor
- ✓ Tarayıcı otomatik açılıyor
- ✓ Statik dosyalar serve ediliyor

### 3. `check_setup.py` Kurulum Kontrol Betiği Oluşturuldu

**Kontrol Edilen Öğeler:**
- ✓ Python bağımlılıkları (fastapi, uvicorn, httpx, sgp4, cv2, numpy, hypothesis, pytest)
- ✓ Gerekli dosyalar (main.py, camera_service.py, routers, frontend, vb.)
- ✓ Port kullanılabilirliği (8000, 8001)

**Çalıştırma:**
```bash
python check_setup.py
```

### 4. `run.sh` Linux/macOS Betiği İyileştirildi

**Eklenen Özellikler:**
- ✓ Kurulum kontrol yapılıyor
- ✓ Hata mesajları gösteriliyor
- ✓ macOS'ta tarayıcı otomatik açılıyor
- ✓ Daha iyi hata yönetimi

### 5. `SETUP.md` Rehberi Oluşturuldu

**İçerik:**
- ✓ Hızlı başlangıç talimatları
- ✓ Kurulum adımları
- ✓ Sorun giderme rehberi
- ✓ API endpoint'leri
- ✓ Dosya yapısı

## Şimdi Nasıl Çalışıyor

### Windows
```bash
run.bat
```
1. Kurulum kontrol yapılıyor
2. Backend başlatılıyor (8000)
3. Kamera Servisi başlatılıyor (8001)
4. Frontend tarayıcıda açılıyor
5. Hata mesajları görünüyor

### Linux/macOS
```bash
./run.sh
```
1. Kurulum kontrol yapılıyor
2. Backend başlatılıyor (8000)
3. Kamera Servisi başlatılıyor (8001)
4. macOS'ta tarayıcı açılıyor
5. Hata mesajları görünüyor

## Test Etme

### Manuel Test
```bash
# Terminal 1
python main.py

# Terminal 2
python camera_service.py

# Terminal 3 - Tarayıcıda
http://127.0.0.1:8000
```

### Otomatik Test
```bash
python check_setup.py
```

## Sonuç

Artık:
- ✓ Backend, Kamera Servisi ve Frontend aynı anda çalışıyor
- ✓ Hata mesajları görünüyor
- ✓ Kurulum sorunları tespit ediliyor
- ✓ Tarayıcı otomatik açılıyor
- ✓ Servisler stabil kalıyor
