# Gereksinimler Belgesi

## Giriş

OrbitGuard, Türk uydularına (Türksat 4A/4B/5A/5B ve Göktürk 1/2) yaklaşan uzay çöpü ve diğer nesneleri gerçek zamanlı olarak takip eden, çarpışma riski hesaplayan, 3D globe üzerinde görselleştiren ve webcam ile gökyüzünden uydu geçişi algılayan bir uzay takip uygulamasıdır.

Sistem üç ana bileşenden oluşur:
- **Backend API** (Python/FastAPI, port 8000): Uydu verisi, konum hesaplama ve konjunksiyon analizi
- **Kamera Servisi** (Python/FastAPI, port 8001): Webcam tabanlı gökyüzü geçiş algılama
- **Frontend** (Tek HTML dosyası, Vanilla JS + Three.js r128): 3D görselleştirme ve kullanıcı arayüzü

---

## Sözlük

- **Backend**: Python/FastAPI tabanlı ana API sunucusu, port 8000
- **Kamera_Servisi**: Python/FastAPI tabanlı bağımsız kamera işleme sunucusu, port 8001
- **Frontend**: Tek HTML dosyasından oluşan Vanilla JS + Three.js r128 tabanlı kullanıcı arayüzü
- **CelesTrak_İstemcisi**: CelesTrak GP API ile iletişim kuran modül
- **SGP4_Motoru**: sgp4 kütüphanesi ile uydu konum hesaplama modülü
- **Konjunksiyon_Motoru**: İki uydu arasındaki yaklaşma mesafesi ve çarpışma riski hesaplama modülü
- **TLE**: Two-Line Element Set — uydu yörünge parametrelerini tanımlayan iki satırlık veri formatı
- **NORAD_ID**: ABD Uzay Komutanlığı tarafından her uzay nesnesine atanan benzersiz katalog numarası
- **GEO**: Geostationary Earth Orbit — Dünya'nın dönüşüyle senkronize, ~35.786 km yüksekliğindeki yörünge
- **LEO**: Low Earth Orbit — 2.000 km altındaki alçak Dünya yörüngesi
- **ECI**: Earth-Centered Inertial — Dünya merkezli atalet referans çerçevesi (km)
- **Geodetik**: Enlem, boylam ve irtifa cinsinden coğrafi konum
- **Konjunksiyon**: İki uzay nesnesinin birbirine belirli bir mesafenin altına yaklaşması olayı
- **Miss_Distance**: Konjunksiyon anında iki nesne arasındaki en yakın mesafe (km)
- **MOG2**: OpenCV Mixture of Gaussians 2 — arka plan çıkarma algoritması
- **MJPEG**: Motion JPEG — sürekli JPEG karelerinden oluşan video akış formatı
- **Semaphore**: Eş zamanlı istek sayısını sınırlayan eşzamanlılık kontrol mekanizması
- **Türk_Uyduları**: TURKSAT 4A (NORAD 39522), TURKSAT 4B (NORAD 40984), TURKSAT 5A (NORAD 47720), TURKSAT 5B (NORAD 49336), GOKTURK-1 (NORAD 41785), GOKTURK-2 (NORAD 40895)

---

## Gereksinimler

### Gereksinim 1: Güvenli Erişim Kontrolü

**Kullanıcı Hikayesi:** Bir sistem yöneticisi olarak, API'ye yalnızca yerel makineden erişilmesini istiyorum; böylece dış ağlardan yetkisiz erişim engellensin.

#### Kabul Kriterleri

1. THE Backend SHALL her gelen HTTP isteğinde kaynak IP adresini doğrulamadan önce başka hiçbir işlem yapmaz.
2. WHEN bir HTTP isteğinin kaynak IP adresi 127.0.0.1 veya ::1 değilse, THEN THE Backend SHALL HTTP 403 Forbidden yanıtı döndürür.
3. WHEN bir HTTP isteğinin kaynak IP adresi 127.0.0.1 veya ::1 ise, THE Backend SHALL isteği normal işlem akışına yönlendirir.
4. THE Kamera_Servisi SHALL her gelen HTTP isteğinde kaynak IP adresini doğrulamadan önce başka hiçbir işlem yapmaz.
5. WHEN bir HTTP isteğinin kaynak IP adresi 127.0.0.1 veya ::1 değilse, THEN THE Kamera_Servisi SHALL HTTP 403 Forbidden yanıtı döndürür.

---

### Gereksinim 2: CelesTrak Veri Erişimi ve Hız Sınırlama

**Kullanıcı Hikayesi:** Bir geliştirici olarak, CelesTrak API'sine aşırı istek gönderilmesini engellemek istiyorum; böylece servis kısıtlamalarına takılmadan güvenilir veri akışı sağlansın.

#### Kabul Kriterleri

1. THE CelesTrak_İstemcisi SHALL CelesTrak GP API'sine gönderilen her HTTP isteğine `User-Agent: OrbitGuard/1.0` başlığını ekler.
2. THE CelesTrak_İstemcisi SHALL CelesTrak GP API'sine yapılan eş zamanlı istek sayısını Semaphore ile dakikada en fazla 10 ile sınırlar.
3. WHEN CelesTrak GP API'sine yapılan bir istek 90 saniye içinde yanıt dönmezse, THEN THE CelesTrak_İstemcisi SHALL isteği iptal eder ve zaman aşımı hatası döndürür.
4. IF CelesTrak GP API erişilemez durumdaysa, THEN THE CelesTrak_İstemcisi SHALL hata mesajını loglayarak çağıran modüle hata bildirir.

---

### Gereksinim 3: Uydu Verisi Önbellekleme

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, uydu verilerinin hızlı yüklenmesini istiyorum; böylece her istekte CelesTrak'a gidilmeden anlık veriye erişebileyim.

#### Kabul Kriterleri

1. THE Backend SHALL grup sorgularından dönen TLE verilerini bellekte en az 15 dakika önbellekte tutar.
2. WHEN bir grup sorgusu için önbellekteki verinin yaşı 15 dakikayı geçmişse, THEN THE Backend SHALL CelesTrak_İstemcisi aracılığıyla veriyi yeniler.
3. THE Backend SHALL tekil uydu sorgularından dönen TLE verilerini bellekte en az 5 dakika önbellekte tutar.
4. WHEN bir tekil uydu sorgusu için önbellekteki verinin yaşı 5 dakikayı geçmişse, THEN THE Backend SHALL CelesTrak_İstemcisi aracılığıyla veriyi yeniler.
5. THE Backend SHALL önbellek deposu olarak Python dict veri yapısını kullanır.

---

### Gereksinim 4: Temel API Sağlık Kontrolleri

**Kullanıcı Hikayesi:** Bir operatör olarak, sistemin çalışır durumda olup olmadığını hızlıca kontrol etmek istiyorum; böylece sorunları erken tespit edebileyim.

#### Kabul Kriterleri

1. WHEN `GET /` isteği alındığında, THE Backend SHALL `{"status": "ok", "version": "1.0"}` JSON yanıtını döndürür.
2. WHEN `GET /health` isteği alındığında, THE Backend SHALL `{"status": "ok", "celestrak_ok": <bool>, "timestamp": "<ISO8601>"}` formatında JSON yanıtı döndürür.
3. WHEN `GET /health` isteği alındığında ve CelesTrak GP API erişilebilir durumdaysa, THE Backend SHALL `celestrak_ok` alanını `true` olarak döndürür.
4. WHEN `GET /health` isteği alındığında ve CelesTrak GP API erişilemez durumdaysa, THE Backend SHALL `celestrak_ok` alanını `false` olarak döndürür.

---

### Gereksinim 5: Uydu Arama

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, uyduları isim veya katalog numarasıyla aramak istiyorum; böylece ilgilendiğim uyduyu hızlıca bulabileyim.

#### Kabul Kriterleri

1. WHEN `GET /api/search/name?q=<sorgu>&format=json` isteği alındığında, THE Backend SHALL adında sorgu dizesini içeren tüm uyduların TLE verilerini JSON formatında döndürür.
2. WHEN `GET /api/search/catnr?id=<norad_id>&format=json` isteği alındığında, THE Backend SHALL belirtilen NORAD_ID'ye sahip uydunun TLE verisini JSON formatında döndürür.
3. WHEN arama sorgusuna eşleşen uydu bulunamazsa, THEN THE Backend SHALL boş liste içeren geçerli bir JSON yanıtı döndürür.
4. IF arama parametresi eksik veya geçersizse, THEN THE Backend SHALL HTTP 400 Bad Request yanıtı döndürür.

---

### Gereksinim 6: Tekil Uydu Bilgisi

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, belirli bir uydunun yörünge parametrelerini görmek istiyorum; böylece uydunun teknik özelliklerini anlayabileyim.

#### Kabul Kriterleri

1. WHEN `GET /api/satellite/{catnr}` isteği alındığında, THE Backend SHALL aşağıdaki alanları içeren JSON yanıtı döndürür: `name`, `norad_id`, `epoch`, `inclination`, `eccentricity`, `altitude_km`, `period_min`, `orbit_type`, `tle_line1`, `tle_line2`.
2. WHEN `GET /api/satellite/{catnr}/position` isteği alındığında, THE Backend SHALL SGP4_Motoru kullanarak anlık ECI koordinatlarını `{eci: {x, y, z}, geodetic: {lat, lon, alt_km}, velocity: {vx, vy, vz}}` formatında döndürür.
3. WHEN `GET /api/satellite/{catnr}/orbital` isteği alındığında, THE Backend SHALL `{perigee_km, apogee_km, period_min, inclination_deg, orbit_type}` alanlarını içeren JSON yanıtı döndürür.
4. IF belirtilen `catnr` değerine sahip uydu bulunamazsa, THEN THE Backend SHALL HTTP 404 Not Found yanıtı döndürür.

---

### Gereksinim 7: Uydu Grubu Sorguları

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, belirli kategorilerdeki tüm uyduları listelemek istiyorum; böylece uzay trafiğini grup bazında izleyebileyim.

#### Kabul Kriterleri

1. WHEN `GET /api/groups/{group}?format=json&limit=500` isteği alındığında, THE Backend SHALL CelesTrak_İstemcisi aracılığıyla ilgili grubun TLE verilerini en fazla 500 kayıtla sınırlı olarak JSON formatında döndürür.
2. WHEN `GET /api/groups/{group}/count` isteği alındığında, THE Backend SHALL ilgili gruptaki uydu sayısını `{"group": "<group>", "count": <int>}` formatında döndürür.
3. IF belirtilen grup adı CelesTrak tarafından desteklenmiyorsa, THEN THE Backend SHALL HTTP 404 Not Found yanıtı döndürür.

---

### Gereksinim 8: SGP4 Konum Hesaplama

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, uyduların anlık konumlarının doğru hesaplanmasını istiyorum; böylece gerçek zamanlı takip yapılabilsin.

#### Kabul Kriterleri

1. THE SGP4_Motoru SHALL sgp4 Python kütüphanesini kullanarak TLE verisinden uydu konumunu ECI koordinat sisteminde hesaplar.
2. WHEN bir TLE verisi SGP4_Motoru'na verildiğinde, THE SGP4_Motoru SHALL ECI koordinatlarını (x, y, z km) ve hız vektörünü (vx, vy, vz km/s) döndürür.
3. THE SGP4_Motoru SHALL ECI koordinatlarını geodetik koordinatlara (enlem derece, boylam derece, irtifa km) dönüştürür.
4. IF TLE verisi geçersiz veya bozuksa, THEN THE SGP4_Motoru SHALL hata mesajıyla birlikte hesaplama hatası bildirir.

---

### Gereksinim 9: Konjunksiyon Analizi — Türk Uyduları

**Kullanıcı Hikayesi:** Bir uzay operatörü olarak, Türk uydularına yaklaşan nesneleri önceden tespit etmek istiyorum; böylece çarpışma riskine karşı önlem alabileyim.

#### Kabul Kriterleri

1. WHEN `GET /api/conjunction/turkish-satellites` isteği alındığında, THE Konjunksiyon_Motoru SHALL 6 Türk uydusunun her biri için önümüzdeki 7 günlük yörünge propagasyonunu 60 saniyelik adımlarla hesaplar.
2. THE Konjunksiyon_Motoru SHALL propagasyon sırasında inklinasyon farkı 5 dereceden büyük olan nesne çiftlerini hızlı filtre aşamasında eleyerek hesaplama süresini azaltır.
3. THE Konjunksiyon_Motoru SHALL filtreden geçen nesne çiftleri için Miss_Distance değerini hesaplar.
4. WHEN `GET /api/conjunction/pair?sat1=<norad1>&sat2=<norad2>&days=7` isteği alındığında, THE Konjunksiyon_Motoru SHALL belirtilen iki uydu arasındaki 7 günlük konjunksiyon analizini döndürür.
5. IF belirtilen NORAD_ID'lerden biri bulunamazsa, THEN THE Konjunksiyon_Motoru SHALL HTTP 404 Not Found yanıtı döndürür.

---

### Gereksinim 10: Kamera Servisi — Hareket Algılama

**Kullanıcı Hikayesi:** Bir gözlemci olarak, webcam ile gökyüzünden geçen uyduları tespit etmek istiyorum; böylece görsel doğrulama yapabileyim.

#### Kabul Kriterleri

1. THE Kamera_Servisi SHALL OpenCV MOG2 arka plan çıkarma algoritmasını kullanarak webcam görüntüsündeki hareketli nesneleri algılar.
2. WHEN `POST /camera/start` isteği alındığında, THE Kamera_Servisi SHALL webcam akışını başlatır ve hareket algılamayı etkinleştirir.
3. WHEN `POST /camera/stop` isteği alındığında, THE Kamera_Servisi SHALL webcam akışını durdurur ve kaynakları serbest bırakır.
4. WHEN `GET /camera/stream` isteği alındığında, THE Kamera_Servisi SHALL MJPEG formatında sürekli video akışı sağlar.
5. WHEN `GET /camera/status` isteği alındığında, THE Kamera_Servisi SHALL kameranın aktif/pasif durumunu ve varsayılan gözlemci konumunu (Ankara: 39.9°N, 32.8°E, 938m) JSON formatında döndürür.
6. WHEN `GET /camera/detections` isteği alındığında, THE Kamera_Servisi SHALL algılanan hareketli nesnelerin listesini zaman damgasıyla birlikte döndürür.

---

### Gereksinim 11: Kamera Proxy Endpoint

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, kamera durumuna ana API üzerinden erişmek istiyorum; böylece tek bir arayüzden tüm sistemi yönetebileyim.

#### Kabul Kriterleri

1. WHEN `GET /api/camera/status` isteği Backend'e alındığında, THE Backend SHALL isteği Kamera_Servisi'nin `GET /camera/status` endpoint'ine proxy olarak iletir.
2. IF Kamera_Servisi erişilemez durumdaysa, THEN THE Backend SHALL HTTP 503 Service Unavailable yanıtı döndürür.

---

### Gereksinim 12: 3D Globe Görselleştirme

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, uyduların konumlarını 3D dünya küresi üzerinde görmek istiyorum; böylece uzaysal ilişkileri sezgisel olarak anlayabileyim.

#### Kabul Kriterleri

1. THE Frontend SHALL Three.js r128 CDN kütüphanesini kullanarak 3D interaktif dünya küresi oluşturur.
2. THE Frontend SHALL Türk_Uyduları'nın anlık konumlarını 3D globe üzerinde ayrı renkli noktalar olarak gösterir.
3. THE Frontend SHALL uydu konumlarını 30 saniyede bir Backend'den alarak 3D globe üzerindeki konumları günceller.
4. THE Frontend SHALL konjunksiyon riski yüksek olan uydu çiftlerini görsel olarak vurgular.
5. THE Frontend SHALL kullanıcının 3D globe'u fare ile döndürmesine, yakınlaştırmasına ve uzaklaştırmasına izin verir.

---

### Gereksinim 13: Kullanıcı Arayüzü Panelleri

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, uydu bilgilerini ve risk durumunu düzenli paneller halinde görmek istiyorum; böylece kritik bilgilere hızlıca ulaşabileyim.

#### Kabul Kriterleri

1. THE Frontend SHALL sol panelde Türk_Uyduları listesini ve uydu tipi (GEO/LEO) ile risk durumuna göre filtreleme seçeneklerini gösterir.
2. THE Frontend SHALL sağ panelde aktif konjunksiyon risklerini önem sırasına göre sıralanmış risk dashboard'u olarak gösterir.
3. WHEN kullanıcı sol panelden bir uydu seçtiğinde, THE Frontend SHALL sağ panelde seçili uydunun detay bilgilerini (isim, NORAD_ID, yörünge tipi, irtifa, periyot, inklinasyon) gösterir.
4. THE Frontend SHALL footer bölümünde kamera akışını ve kamera servisinin durum bilgisini gösterir.
5. THE Frontend SHALL koyu tema renk paleti kullanır; arka plan rengi #0a0a0f olur.

---

### Gereksinim 14: Tek Dosya Frontend Mimarisi

**Kullanıcı Hikayesi:** Bir geliştirici olarak, frontend'in tek bir HTML dosyasında bulunmasını istiyorum; böylece dağıtım ve bakım basit kalsın.

#### Kabul Kriterleri

1. THE Frontend SHALL tüm HTML yapısını, CSS stillerini ve JavaScript kodunu tek bir `index.html` dosyasında barındırır.
2. THE Frontend SHALL Three.js r128 kütüphanesini CDN üzerinden yükler; yerel dosya kullanmaz.
3. THE Frontend SHALL harici CSS dosyası veya harici JavaScript dosyası kullanmaz; tüm stiller inline olarak tanımlanır.
4. THE Frontend SHALL Backend API'sine yalnızca `http://127.0.0.1:8000` adresinden istek gönderir.

---

### Gereksinim 15: Başlatma Betikleri

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, uygulamayı tek komutla başlatmak istiyorum; böylece kurulum ve çalıştırma süreci basit olsun.

#### Kabul Kriterleri

1. THE Backend SHALL `run.sh` (Linux/macOS) ve `run.bat` (Windows) betikleri aracılığıyla başlatılabilir.
2. WHEN `run.sh` veya `run.bat` çalıştırıldığında, THE Backend SHALL port 8000'de yalnızca 127.0.0.1 arayüzünü dinleyerek başlar.
3. WHEN `run.sh` veya `run.bat` çalıştırıldığında, THE Kamera_Servisi SHALL port 8001'de yalnızca 127.0.0.1 arayüzünü dinleyerek başlar.
4. THE Backend SHALL tüm Python bağımlılıklarını `requirements.txt` dosyasında listeler.
