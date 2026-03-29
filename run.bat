@echo off
REM OrbitGuard Başlatma Betiği (Windows)
REM Kullanım: run.bat

setlocal enabledelayedexpansion

echo.
echo ========================================
echo OrbitGuard Başlatılıyor
echo ========================================
echo.

REM Kurulum kontrolü
echo Kurulum kontrol ediliyor...
python check_setup.py
if errorlevel 1 (
    echo.
    echo HATA: Kurulum kontrol başarısız!
    echo Lütfen eksik bağımlılıkları yükleyin:
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo Servisler Başlatılıyor
echo ========================================
echo.

REM Backend'i ayrı pencerede başlat (127.0.0.1:8000)
echo Backend başlatılıyor: http://127.0.0.1:8000
start "OrbitGuard Backend" cmd /k "python main.py"

REM Kamera Servisi'ni ayrı pencerede başlat (127.0.0.1:8001)
echo Kamera Servisi başlatılıyor: http://127.0.0.1:8001
start "OrbitGuard Camera" cmd /k "python camera_service.py"

REM Frontend açılıyor
echo Frontend açılıyor...
timeout /t 3 /nobreak
start http://127.0.0.1:8000

echo.
echo ========================================
echo Servisler Çalışıyor
echo ========================================
echo.
echo   Backend        -^> http://127.0.0.1:8000
echo   Kamera Servisi -^> http://127.0.0.1:8001
echo.
echo Servisleri durdurmak için ilgili pencereleri kapatın.
echo.
pause
