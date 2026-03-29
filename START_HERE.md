# OrbitGuard — Başlangıç Rehberi

## ✓ Kurulum Başarılı!

Tüm kontroller geçti. OrbitGuard artık çalışmaya hazır.

```
✓ FastAPI
✓ Uvicorn
✓ HTTPX
✓ SGP4
✓ OpenCV
✓ NumPy
✓ Hypothesis
✓ Pytest
✓ Port 8000 — Kullanılabilir
✓ Port 8001 — Kullanılabilir
✓ Tüm dosyalar mevcut
```

## 🚀 Hızlı Başlangıç

### Windows
```bash
run.bat
```

### Linux/macOS
```bash
chmod +x run.sh
./run.sh
```

## 📋 Ne Olacak

1. **Kurulum Kontrol** — Bağımlılıklar ve dosyalar doğrulanacak
2. **Backend Başlat** — http://127.0.0.1:8000 (Uydu API)
3. **Kamera Servisi Başlat** — http://127.0.0.1:8001 (Webcam)
4. **Frontend Aç** — Tarayıcıda 3D Globe görünecek

## 🌐 Erişim Adresleri

| Servis | URL | Açıklama |
|--------|-----|----------|
| Frontend | http://127.0.0.1:8000 | 3D Uydu Takip Sistemi |
| Backend API | http://127.0.0.1:8000/api | Uydu Verileri |
| Kamera | http://127.0.0.1:8001 | Webcam Akışı |
| Sağlık | http://127.0.0.1:8000/health | Sistem Durumu |

## 🎮 Frontend Kullanımı

### Sol Panel — Uydu Listesi
- 6 Türk uydusu listelenir
- GEO/LEO filtresi
- Risk durumu gösterilir

### Orta — 3D Globe
- Dünya küresi
- Uydu noktaları
- Fare ile döndür/yakınlaştır

### Sağ Panel — Risk Dashboard
- Konjunksiyon riskleri
- CRITICAL → HIGH → MEDIUM → LOW sırası
- Seçili uydu detayları

### Alt — Kamera Footer
- Webcam MJPEG akışı
- Kamera durumu
- Hareket algılamaları

## 🔧 API Endpoint'leri

### Uydu Araması
```bash
# İsim araması
curl http://127.0.0.1:8000/api/search/name?q=TURKSAT

# NORAD_ID araması
curl http://127.0.0.1:8000/api/search/catnr?id=39522
```

### Uydu Bilgisi
```bash
# Uydu detayları
curl http://127.0.0.1:8000/api/satellite/39522

# Anlık konum
curl http://127.0.0.1:8000/api/satellite/39522/position

# Yörünge parametreleri
curl http://127.0.0.1:8000/api/satellite/39522/orbital
```

### Konjunksiyon Analizi
```bash
# Türk uyduları konjunksiyon
curl http://127.0.0.1:8000/api/conjunction/turkish-satellites

# İki uydu arası konjunksiyon
curl http://127.0.0.1:8000/api/conjunction/pair?sat1=39522&sat2=40984&days=7
```

### Kamera
```bash
# Kamerayı başlat
curl -X POST http://127.0.0.1:8001/camera/start

# Kamerayı durdur
curl -X POST http://127.0.0.1:8001/camera/stop

# Kamera durumu
curl http://127.0.0.1:8001/camera/status

# Algılanan nesneler
curl http://127.0.0.1:8001/camera/detections
```

## 🧪 Test Çalıştırma

```bash
# Tüm testleri çalıştır
pytest tests/ -v

# Belirli test dosyasını çalıştır
pytest tests/test_middleware.py -v

# Özellik testlerini çalıştır
pytest tests/ -v -k "property"
```

## 📊 Türk Uyduları

| Uydu | NORAD_ID | Yörünge | Durum |
|------|----------|--------|-------|
| TURKSAT 4A | 39522 | GEO | Aktif |
| TURKSAT 4B | 40984 | GEO | Aktif |
| TURKSAT 5A | 47720 | GEO | Aktif |
| TURKSAT 5B | 49336 | GEO | Aktif |
| GOKTURK-1 | 41785 | LEO | Aktif |
| GOKTURK-2 | 40895 | LEO | Aktif |

## 🐛 Sorun Giderme

### Hata Mesajı Görülmüyor
```bash
# Manuel başlat
python main.py
python camera_service.py
```

### Port Kullanımda
```bash
# Windows
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :8000
```

### Bağımlılık Eksik
```bash
python check_setup.py
pip install -r requirements.txt
```

### Kapsamlı Tanı
```bash
# Windows
diagnose.bat

# Linux/macOS
./diagnose.sh
```

## 📚 Dokümantasyon

- **SETUP.md** — Kurulum rehberi
- **TROUBLESHOOTING.md** — Sorun giderme
- **FIXES.md** — Yapılan düzeltmeler
- **README_FIXES.md** — Sorun çözümleri özeti

## 🎯 Sonraki Adımlar

1. **Uygulamayı Başlat**
   ```bash
   run.bat  # Windows
   ./run.sh # Linux/macOS
   ```

2. **Frontend'i Keşfet**
   - 3D Globe'u döndür
   - Uyduları seç
   - Kamera akışını izle

3. **API'yi Test Et**
   ```bash
   curl http://127.0.0.1:8000/health
   ```

4. **Testleri Çalıştır**
   ```bash
   pytest tests/ -v
   ```

5. **Geliştirmeye Başla**
   - Yeni router ekle
   - Yeni test yaz
   - Özellik ekle

## ✨ Başarılı Kurulum Belirtileri

✓ `python check_setup.py` başarılı
✓ `run.bat` veya `./run.sh` 3 pencere açıyor
✓ Backend: http://127.0.0.1:8000 çalışıyor
✓ Kamera: http://127.0.0.1:8001 çalışıyor
✓ Frontend: Tarayıcıda açılıyor
✓ 3D Globe görünüyor
✓ Uydu noktaları görünüyor
✓ Kamera akışı görünüyor

## 🎉 Tebrikler!

OrbitGuard kurulumu başarıyla tamamlandı. Artık Türk uydularını gerçek zamanlı olarak izleyebilirsiniz!

---

**Sorular mı var?** Bkz. TROUBLESHOOTING.md
