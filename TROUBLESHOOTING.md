# OrbitGuard Sorun Giderme Rehberi

## Hızlı Tanı

### Windows
```bash
diagnose.bat
```

### Linux/macOS
```bash
chmod +x diagnose.sh
./diagnose.sh
```

---

## Yaygın Sorunlar ve Çözümleri

### 1. Backend/Kamera Penceresi Hemen Kapanıyor

**Belirtiler:**
- `run.bat` çalıştırıldığında pencereler açılıp hemen kapanıyor
- Hata mesajı görülmüyor

**Çözüm:**

**Adım 1:** Kurulum kontrol et
```bash
python check_setup.py
```

**Adım 2:** Eksik bağımlılıkları yükle
```bash
pip install -r requirements.txt
```

**Adım 3:** Manuel başlat (hataları görmek için)
```bash
# Terminal 1
python main.py

# Terminal 2
python camera_service.py
```

**Adım 4:** Hata mesajını oku ve çöz

---

### 2. "Port Already in Use" Hatası

**Belirtiler:**
```
Address already in use
OSError: [Errno 48] Address already in use
```

**Çözüm:**

**Windows:**
```bash
# Port 8000'i kullanan işlemi bul
netstat -ano | findstr :8000

# Sonuç örneği: TCP 127.0.0.1:8000 LISTENING 1234
# PID = 1234

# İşlemi kapat
taskkill /PID 1234 /F
```

**Linux/macOS:**
```bash
# Port 8000'i kullanan işlemi bul
lsof -i :8000

# Sonuç örneği: python 1234 user 3u IPv4 0x... 0t0 TCP 127.0.0.1:8000 (LISTEN)
# PID = 1234

# İşlemi kapat
kill -9 1234
```

---

### 3. "ModuleNotFoundError" Hatası

**Belirtiler:**
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'cv2'
```

**Çözüm:**

```bash
# Bağımlılıkları yeniden yükle
pip install --upgrade -r requirements.txt

# Veya belirli modülü yükle
pip install fastapi
pip install opencv-python
pip install sgp4
```

---

### 4. Webcam Açılmıyor

**Belirtiler:**
```
Webcam unavailable (HTTP 503)
cv2.error: (-215:Assertion failed) !_src.empty()
```

**Çözüm:**

**Windows:**
1. Kamera Uygulaması'nı kapatın
2. Başka bir uygulama webcam kullanmıyor mu kontrol edin
3. Cihaz Yöneticisi'nde kamera sürücüsünü kontrol edin

**Linux:**
```bash
# Webcam cihazını kontrol et
ls -la /dev/video0

# Izinleri kontrol et
sudo usermod -a -G video $USER

# Yeniden giriş yap
```

**macOS:**
1. Sistem Tercihleri → Güvenlik ve Gizlilik → Kamera
2. Python'a kamera erişim izni ver

---

### 5. Frontend Açılmıyor

**Belirtiler:**
```
Tarayıcı açılmıyor
http://127.0.0.1:8000 erişilemiyor
```

**Çözüm:**

**Adım 1:** Backend çalışıyor mu kontrol et
```bash
# Terminal'de Backend çalışıyor mu görmek için
python main.py
```

**Adım 2:** Tarayıcıda manuel aç
```
http://127.0.0.1:8000
```

**Adım 3:** Frontend dosyası var mı kontrol et
```bash
ls -la frontend/index.html
```

---

### 6. CelesTrak Bağlantı Hatası

**Belirtiler:**
```
CelesTrak erişilemez
celestrak_ok: false
```

**Çözüm:**

**Adım 1:** İnternet bağlantısını kontrol et
```bash
ping celestrak.org
```

**Adım 2:** Firewall/Proxy kontrol et
- Kurumsal ağda mısınız?
- Proxy ayarları doğru mu?

**Adım 3:** CelesTrak API durumunu kontrol et
```bash
curl -H "User-Agent: OrbitGuard/1.0" https://celestrak.org/NORAD/elements/active.txt
```

---

### 7. Kamera Akışı Görülmüyor

**Belirtiler:**
```
Kamera footer'ında siyah ekran
MJPEG akışı yüklenmedi
```

**Çözüm:**

**Adım 1:** Kamera servisi çalışıyor mu kontrol et
```bash
curl http://127.0.0.1:8001/camera/status
```

**Adım 2:** Kamerayı başlat
```bash
curl -X POST http://127.0.0.1:8001/camera/start
```

**Adım 3:** Akışı test et
```bash
curl http://127.0.0.1:8001/camera/stream
```

---

### 8. Uydu Konumu Güncellenmedi

**Belirtiler:**
```
3D Globe'da uydu noktaları hareket etmiyor
Konum verisi alınamıyor
```

**Çözüm:**

**Adım 1:** API endpoint'ini test et
```bash
curl http://127.0.0.1:8000/api/satellite/39522/position
```

**Adım 2:** CelesTrak bağlantısını kontrol et
```bash
curl http://127.0.0.1:8000/health
```

**Adım 3:** Tarayıcı konsolunu kontrol et
- F12 → Console
- Hata mesajları var mı?

---

### 9. Konjunksiyon Analizi Çalışmıyor

**Belirtiler:**
```
Risk Dashboard boş
Konjunksiyon verisi yüklenmedi
```

**Çözüm:**

**Adım 1:** Endpoint'i test et
```bash
curl http://127.0.0.1:8000/api/conjunction/turkish-satellites
```

**Adım 2:** Türk uyduları verisi var mı kontrol et
```bash
curl http://127.0.0.1:8000/api/satellite/39522
```

**Adım 3:** Tarayıcı konsolunu kontrol et
- Hata mesajları var mı?

---

### 10. Test Başarısız Oluyor

**Belirtiler:**
```
pytest başarısız
AssertionError: ...
```

**Çözüm:**

**Adım 1:** Tüm testleri çalıştır
```bash
pytest tests/ -v
```

**Adım 2:** Belirli test dosyasını çalıştır
```bash
pytest tests/test_middleware.py -v
```

**Adım 3:** Hata mesajını oku
```bash
pytest tests/ -v -s
```

---

## Tanı Araçları

### check_setup.py
Tüm bağımlılıkları ve dosyaları kontrol eder.
```bash
python check_setup.py
```

### diagnose.bat (Windows)
Kapsamlı tanı yapır.
```bash
diagnose.bat
```

### diagnose.sh (Linux/macOS)
Kapsamlı tanı yapır.
```bash
./diagnose.sh
```

---

## Günlük Dosyaları Kontrol Etme

### Backend Günlüğü
```bash
# Terminal'de Backend çalıştırıldığında çıktı görülür
python main.py
```

### Kamera Servisi Günlüğü
```bash
# Terminal'de Kamera Servisi çalıştırıldığında çıktı görülür
python camera_service.py
```

### Tarayıcı Konsolü
1. F12 tuşuna bas
2. Console sekmesine tıkla
3. Hata mesajlarını oku

---

## İletişim ve Destek

Sorun çözemediyseniz:

1. **Tanı çıktısını kaydet**
   ```bash
   python check_setup.py > diagnosis.txt
   ```

2. **Hata mesajını kopyala**
   - Terminal çıktısı
   - Tarayıcı konsolu
   - Günlük dosyaları

3. **Sorun raporla**
   - Tanı çıktısını ekle
   - Hata mesajlarını ekle
   - Adımları açıkla

---

## Başarılı Kurulum Belirtileri

✓ `python check_setup.py` başarılı çalışıyor
✓ `run.bat` veya `./run.sh` 3 pencere açıyor
✓ Backend: http://127.0.0.1:8000 çalışıyor
✓ Kamera: http://127.0.0.1:8001 çalışıyor
✓ Frontend: Tarayıcıda açılıyor
✓ 3D Globe görünüyor
✓ Uydu noktaları görünüyor
✓ Kamera akışı görünüyor

---

## Sonraki Adımlar

Kurulum başarılı olduktan sonra:

1. **Frontend'i keşfet**
   - Sol panel: Uydu listesi
   - Sağ panel: Risk dashboard
   - Orta: 3D Globe
   - Alt: Kamera akışı

2. **API'yi test et**
   ```bash
   curl http://127.0.0.1:8000/health
   ```

3. **Testleri çalıştır**
   ```bash
   pytest tests/ -v
   ```

4. **Geliştirmeye başla**
   - Yeni router ekle
   - Yeni test yaz
   - Özellik ekle
