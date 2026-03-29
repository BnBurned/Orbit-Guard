@echo off
REM OrbitGuard Tanı Betiği (Windows)
REM Sorunları tespit etmek için çalıştırın

setlocal enabledelayedexpansion

echo.
echo ========================================
echo OrbitGuard Tanı Betiği
echo ========================================
echo.

REM Python kontrolü
echo [1/5] Python kontrolü...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ✗ Python yüklü değil!
    echo   Çözüm: https://www.python.org/downloads/
    goto error
) else (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo   ✓ !PYTHON_VERSION!
)

REM Bağımlılıklar kontrolü
echo.
echo [2/5] Bağımlılıklar kontrolü...
python check_setup.py
if errorlevel 1 (
    echo.
    echo   ✗ Bağımlılıklar eksik!
    echo   Çözüm: pip install -r requirements.txt
    goto error
)

REM Port kontrolü
echo.
echo [3/5] Port kontrolü...
netstat -ano | findstr :8000 >nul 2>&1
if errorlevel 1 (
    echo   ✓ Port 8000 kullanılabilir
) else (
    echo   ⚠ Port 8000 kullanımda
    echo   Çözüm: taskkill /PID ^<PID^> /F
)

netstat -ano | findstr :8001 >nul 2>&1
if errorlevel 1 (
    echo   ✓ Port 8001 kullanılabilir
) else (
    echo   ⚠ Port 8001 kullanımda
    echo   Çözüm: taskkill /PID ^<PID^> /F
)

REM Dosya yapısı kontrolü
echo.
echo [4/5] Dosya yapısı kontrolü...
if exist "main.py" (
    echo   ✓ main.py
) else (
    echo   ✗ main.py eksik
    goto error
)

if exist "camera_service.py" (
    echo   ✓ camera_service.py
) else (
    echo   ✗ camera_service.py eksik
    goto error
)

if exist "frontend\index.html" (
    echo   ✓ frontend\index.html
) else (
    echo   ✗ frontend\index.html eksik
    goto error
)

REM Webcam kontrolü
echo.
echo [5/5] Webcam kontrolü...
python -c "import cv2; cap = cv2.VideoCapture(0); print('   ✓ Webcam kullanılabilir' if cap.isOpened() else '   ⚠ Webcam bulunamadı'); cap.release()" 2>nul
if errorlevel 1 (
    echo   ⚠ Webcam kontrol edilemedi
)

echo.
echo ========================================
echo Tanı Tamamlandı
echo ========================================
echo.
echo Tüm kontroller başarılı!
echo OrbitGuard'ı başlatmak için: run.bat
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo HATA
echo ========================================
echo.
pause
exit /b 1
