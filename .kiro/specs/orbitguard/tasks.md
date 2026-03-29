# Uygulama Planı: OrbitGuard

## Genel Bakış

Backend (FastAPI :8000), Kamera Servisi (FastAPI :8001) ve Frontend (tek HTML) bileşenlerini tasarım belgesindeki sıraya göre adım adım inşa edip birbirine bağlayan artımlı bir uygulama planı.

## Görevler

- [x] 1. `requirements.txt` — Python bağımlılıklarını tanımla
  - `fastapi`, `uvicorn[standard]`, `sgp4`, `httpx`, `opencv-python`, `numpy` ve test bağımlılıklarını (`hypothesis`, `pytest`, `pytest-asyncio`, `httpx`) ekle
  - _Gereksinimler: 15.4_

- [x] 2. `middleware.py` — IP erişim kontrolü
  - [x] 2.1 `LocalOnlyMiddleware` sınıfını yaz
    - `BaseHTTPMiddleware` miras al; `dispatch` metodunda `request.client.host` 127.0.0.1 veya ::1 değilse HTTP 403 döndür
    - _Gereksinimler: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 2.2 P1 özellik testi — IP filtresi
    - **Özellik 1: IP Filtresi — Her İki Servis**
    - **Doğrular: Gereksinimler 1.2, 1.3, 1.4, 1.5**
    - `st.ip_addresses()` ile rastgele IP üret; 127.0.0.1/::1 dışındakiler 403 almalı
    - `tests/test_middleware.py`

- [x] 3. `celestrak_client.py` — CelesTrak HTTP istemcisi
  - [x] 3.1 `CelesTrakClient` sınıfını yaz
    - `fetch_group`, `fetch_by_catnr`, `fetch_by_name`, `health_check` metodlarını uygula
    - Her istekte `User-Agent: OrbitGuard/1.0` başlığı ekle; `asyncio.Semaphore(10)` ile eş zamanlı istek sınırla; 90s timeout
    - In-memory cache: grup TTL 900s, tekil TTL 300s (`CacheEntry` dataclass)
    - _Gereksinimler: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_
  - [x] 3.2 P2 özellik testi — User-Agent başlığı
    - **Özellik 2: User-Agent Başlığı Zorunluluğu**
    - **Doğrular: Gereksinim 2.1**
    - Mock HTTP client ile her CelesTrak isteğinde `User-Agent: OrbitGuard/1.0` doğrula
    - `tests/test_celestrak_client.py`
  - [x] 3.3 P3 özellik testi — Eş zamanlı istek sınırı
    - **Özellik 3: Eş Zamanlı İstek Sınırı**
    - **Doğrular: Gereksinim 2.2**
    - N>10 eş zamanlı istek gönder; aktif istek sayısının 10'u geçmediğini doğrula
    - `tests/test_celestrak_client.py`
  - [x] 3.4 P4 özellik testi — Önbellek TTL doğruluğu
    - **Özellik 4: Önbellek TTL Doğruluğu**
    - **Doğrular: Gereksinimler 3.1, 3.2, 3.3, 3.4**
    - `st.floats(0, 1800)` ile zaman manipülasyonu; TTL dolmadan cache hit, dolduktan sonra cache miss
    - `tests/test_celestrak_client.py`

- [x] 4. `sgp4_engine.py` — SGP4 konum hesaplama motoru
  - [x] 4.1 `SGP4Engine` sınıfını yaz
    - `propagate(tle_line1, tle_line2, dt)` → ECI (x,y,z km) + hız (vx,vy,vz km/s)
    - `eci_to_geodetic(x, y, z, dt)` → (lat, lon, alt_km)
    - `orbital_elements(tle_line1, tle_line2)` → perigee, apogee, period, inclination
    - Geçersiz TLE → `ValueError`; propagasyon hatası → `PropagationError`; dönüşüm hatası → `CoordinateError`
    - _Gereksinimler: 8.1, 8.2, 8.3, 8.4_
  - [x] 4.2 P11 özellik testi — SGP4 çıktı şeması ve koordinat geçerliliği
    - **Özellik 11: SGP4 Çıktı Şeması ve Koordinat Geçerliliği**
    - **Doğrular: Gereksinimler 8.1, 8.2, 8.3**
    - Geçerli TLE üret; enlem ∈ [-90,90], boylam ∈ [-180,180], irtifa ≥ 0 doğrula
    - `tests/test_sgp4_engine.py`
  - [x] 4.3 P12 özellik testi — Geçersiz TLE → hata
    - **Özellik 12: Geçersiz TLE → Hata**
    - **Doğrular: Gereksinim 8.4**
    - `st.text()` ile bozuk TLE gönder; exception fırlatıldığını doğrula
    - `tests/test_sgp4_engine.py`

- [x] 5. `conjunction.py` — Konjunksiyon analiz motoru
  - [x] 5.1 `ConjunctionEngine` sınıfını yaz
    - `analyze_turkish_satellites(debris_tles)` → 6 Türk uydusu × debris, 7 gün, 60s adım
    - `analyze_pair(tle1, tle2, days)` → konjunksiyon olayları listesi
    - `_inclination_filter(sat1, sat2)` → inklinasyon farkı > 5° ise `True` (elenecek)
    - `_compute_miss_distance(pos1, pos2)` → Öklid mesafesi km
    - Risk seviyesi: CRITICAL (<1km), HIGH (<5km), MEDIUM (<10km), LOW (≥10km)
    - _Gereksinimler: 9.1, 9.2, 9.3, 9.4, 9.5_
  - [x] 5.2 P13 özellik testi — İnklinasyon filtresi doğruluğu
    - **Özellik 13: İnklinasyon Filtresi Doğruluğu**
    - **Doğrular: Gereksinim 9.2**
    - `st.floats()` ile inklinasyon farkı > 5° olan çiftler; sonuçta yer almadığını doğrula
    - `tests/test_conjunction.py`
  - [x] 5.3 P14 özellik testi — Miss distance alanı
    - **Özellik 14: Konjunksiyon Olayı Miss Distance Alanı**
    - **Doğrular: Gereksinim 9.3**
    - Her konjunksiyon olayında `miss_distance_km` ≥ 0 olduğunu doğrula
    - `tests/test_conjunction.py`

- [x] 6. `routers/search.py` — Uydu arama router'ı
  - [x] 6.1 Search router'ını yaz
    - `GET /api/search/name?q=<sorgu>&format=json` → isim araması
    - `GET /api/search/catnr?id=<norad_id>&format=json` → NORAD_ID araması
    - Eksik/geçersiz parametre → 400; sonuç yok → `[]`
    - _Gereksinimler: 5.1, 5.2, 5.3, 5.4_
  - [x] 6.2 P6 özellik testi — İsim araması tutarlılığı
    - **Özellik 6: İsim Araması Tutarlılığı**
    - **Doğrular: Gereksinim 5.1**
    - `st.text()` ile rastgele sorgu; dönen tüm uyduların `name` alanı sorguyu içermeli
    - `tests/test_search.py`
  - [x] 6.3 P7 özellik testi — NORAD_ID araması doğruluğu
    - **Özellik 7: NORAD_ID Araması Doğruluğu**
    - **Doğrular: Gereksinim 5.2**
    - `st.integers(1, 99999)` ile NORAD_ID; dönen `norad_id` alanı sorgulananla eşleşmeli
    - `tests/test_search.py`
  - [x] 6.4 P8 özellik testi — Geçersiz parametre → 400
    - **Özellik 8: Geçersiz Parametre → 400**
    - **Doğrular: Gereksinim 5.4**
    - Eksik parametre ile istek gönder; HTTP 400 döndüğünü doğrula
    - `tests/test_search.py`

- [x] 7. `routers/satellite.py` — Tekil uydu router'ı
  - [x] 7.1 Satellite router'ını yaz
    - `GET /api/satellite/{catnr}` → uydu bilgisi (name, norad_id, epoch, inclination, eccentricity, altitude_km, period_min, orbit_type, tle_line1, tle_line2)
    - `GET /api/satellite/{catnr}/position` → ECI + geodetik + hız
    - `GET /api/satellite/{catnr}/orbital` → perigee, apogee, period, inclination, orbit_type
    - Bulunamayan catnr → 404
    - _Gereksinimler: 6.1, 6.2, 6.3, 6.4_
  - [x] 7.2 P9 özellik testi — Uydu endpoint şema bütünlüğü
    - **Özellik 9: Uydu Endpoint Şema Bütünlüğü**
    - **Doğrular: Gereksinimler 6.1, 6.2, 6.3**
    - `st.integers()` ile catnr; tüm zorunlu alanların yanıtta mevcut olduğunu doğrula
    - `tests/test_satellite.py`

- [x] 8. `routers/groups.py` — Grup sorgu router'ı
  - [x] 8.1 Groups router'ını yaz
    - `GET /api/groups/{group}?format=json&limit=500` → grup TLE listesi, max 500 kayıt
    - `GET /api/groups/{group}/count` → `{"group": str, "count": int}`
    - Desteklenmeyen grup → 404
    - _Gereksinimler: 7.1, 7.2, 7.3_
  - [x] 8.2 P10 özellik testi — Grup limit sınırı
    - **Özellik 10: Grup Limit Sınırı**
    - **Doğrular: Gereksinim 7.1**
    - Mock CelesTrak ile herhangi grup sorgusu; dönen kayıt sayısı ≤ 500 olmalı
    - `tests/test_groups.py`

- [x] 9. `routers/conjunction.py` — Konjunksiyon router'ı
  - [x] 9.1 Conjunction router'ını yaz
    - `GET /api/conjunction/turkish-satellites` → 6 Türk uydusu konjunksiyon analizi
    - `GET /api/conjunction/pair?sat1=<norad1>&sat2=<norad2>&days=7` → çift analizi
    - Bulunamayan NORAD_ID → 404
    - _Gereksinimler: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 10. Kontrol noktası — Tüm testlerin geçtiğini doğrula
  - Tüm testlerin geçtiğini doğrula, sorular varsa kullanıcıya sor.

- [x] 11. `main.py` — FastAPI uygulama giriş noktası
  - [x] 11.1 `main.py`'yi yaz
    - `LocalOnlyMiddleware` kaydı; tüm router'ları dahil et
    - `GET /` → `{"status": "ok", "version": "1.0"}`
    - `GET /health` → `{"status": "ok", "celestrak_ok": bool, "timestamp": ISO8601}`
    - `GET /api/camera/status` → Kamera Servisi proxy; erişilemezse 503
    - Uvicorn: `host="127.0.0.1"`, `port=8000`
    - _Gereksinimler: 4.1, 4.2, 4.3, 4.4, 11.1, 11.2, 15.2_
  - [x] 11.2 P5 özellik testi — Sağlık endpoint şeması
    - **Özellik 5: Sağlık Endpoint Şeması**
    - **Doğrular: Gereksinimler 4.2, 4.3, 4.4**
    - Mock CelesTrak ile `GET /health`; `status`, `celestrak_ok`, `timestamp` alanlarını ve CelesTrak korelasyonunu doğrula
    - `tests/test_health.py`

- [x] 12. `camera_service.py` — Bağımsız kamera servisi
  - [x] 12.1 `camera_service.py`'yi yaz
    - `LocalOnlyMiddleware` uygula (port 8001)
    - `POST /camera/start` → webcam aç, MOG2 etkinleştir (history=500, varThreshold=16, detectShadows=True)
    - `POST /camera/stop` → kaynakları serbest bırak
    - `GET /camera/stream` → `multipart/x-mixed-replace` MJPEG akışı
    - `GET /camera/status` → `{active, observer: {name, lat:39.9, lon:32.8, alt_m:938}, detections_count}`
    - `GET /camera/detections` → zaman damgalı algılama listesi
    - Webcam yokken `POST /camera/start` → 503
    - _Gereksinimler: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 15.3_
  - [ ] 12.2 P15 özellik testi — MOG2 hareket algılama
    - **Özellik 15: MOG2 Hareket Algılama**
    - **Doğrular: Gereksinim 10.1**
    - Mock OpenCV frame; hareketsiz → 0 algılama, hareketli → ≥1 algılama
    - `tests/test_camera_service.py`
  - [ ] 12.3 P16 özellik testi — Kamera start/stop round-trip
    - **Özellik 16: Kamera Start/Stop Round-Trip**
    - **Doğrular: Gereksinimler 10.2, 10.3**
    - Start → `active: true`, Stop → `active: false` döngüsünü doğrula
    - `tests/test_camera_service.py`
  - [ ] 12.4 P17 özellik testi — Kamera durum şeması ve Ankara koordinatları
    - **Özellik 17: Kamera Durum Şeması ve Ankara Koordinatları**
    - **Doğrular: Gereksinim 10.5**
    - `GET /camera/status`; `observer.lat` ≈ 39.9, `observer.lon` ≈ 32.8, `observer.alt_m` ≈ 938 doğrula
    - `tests/test_camera_service.py`
  - [ ] 12.5 P18 özellik testi — Detection zaman damgası zorunluluğu
    - **Özellik 18: Detection Zaman Damgası Zorunluluğu**
    - **Doğrular: Gereksinim 10.6**
    - Her detection nesnesinde `timestamp` alanının mevcut olduğunu doğrula
    - `tests/test_camera_service.py`

- [x] 13. `frontend/index.html` — Tek dosya frontend
  - [x] 13.1 HTML iskeletini ve Three.js globe'u yaz
    - Three.js r128 CDN: `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`
    - `GlobeRenderer` sınıfı: 3D dünya küresi, uydu noktaları, fare kontrolü (döndür/yakınlaştır)
    - Arka plan rengi `#0a0a0f`; tüm stiller inline `<style>` bloğunda
    - _Gereksinimler: 12.1, 12.5, 14.1, 14.2, 14.3_
  - [x] 13.2 Panel ve API istemcisini yaz
    - `APIClient` sınıfı: tüm fetch çağrıları `http://127.0.0.1:8000` base URL ile
    - `SatellitePanel` (sol): 6 Türk uydusu listesi, GEO/LEO filtresi
    - `RiskDashboard` (sağ): konjunksiyon riskleri, CRITICAL→HIGH→MEDIUM→LOW sırası
    - `DetailView`: seçili uydu detayları (name, NORAD_ID, orbit_type, altitude, period, inclination)
    - `CameraFooter`: MJPEG akışı + kamera durum göstergesi
    - 30s polling interval ile konum güncelleme
    - _Gereksinimler: 12.2, 12.3, 12.4, 13.1, 13.2, 13.3, 13.4, 13.5, 14.4_
  - [x] 13.3 P19 özellik testi — Risk sıralama tutarlılığı
    - **Özellik 19: Risk Sıralama Tutarlılığı**
    - **Doğrular: Gereksinim 13.2**
    - `st.lists()` ile rastgele risk listesi; CRITICAL>HIGH>MEDIUM>LOW azalan sırasını doğrula
    - `tests/test_frontend.py`
  - [x] 13.4 P20 özellik testi — Frontend API base URL tutarlılığı
    - **Özellik 20: Frontend API Base URL Tutarlılığı**
    - **Doğrular: Gereksinim 14.4**
    - `index.html` içindeki tüm fetch çağrılarının `http://127.0.0.1:8000` ile başladığını doğrula
    - `tests/test_frontend.py`

- [x] 14. `run.bat` ve `run.sh` — Başlatma betikleri
  - [x] 14.1 `run.sh` (Linux/macOS) yaz
    - Backend'i `127.0.0.1:8000`, Kamera Servisi'ni `127.0.0.1:8001` üzerinde başlat
    - _Gereksinimler: 15.1, 15.2, 15.3_
  - [x] 14.2 `run.bat` (Windows) yaz
    - Aynı portları Windows `start` komutu ile başlat
    - _Gereksinimler: 15.1, 15.2, 15.3_

- [x] 15. Son kontrol noktası — Tüm testlerin geçtiğini doğrula
  - Tüm testlerin geçtiğini doğrula, sorular varsa kullanıcıya sor.

## Notlar

- `*` ile işaretli alt görevler isteğe bağlıdır; MVP için atlanabilir
- Her görev belirli gereksinimlere referans verir
- Özellik testleri Hypothesis ile minimum 100 iterasyon çalıştırılmalıdır
- Test dosyaları `tests/` dizininde toplanır
