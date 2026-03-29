#!/usr/bin/env bash
# OrbitGuard Başlatma Betiği (Linux/macOS)
# Kullanım: chmod +x run.sh && ./run.sh

set -e

echo ""
echo "========================================"
echo "OrbitGuard Başlatılıyor"
echo "========================================"
echo ""

# Kurulum kontrolü
echo "Kurulum kontrol ediliyor..."
python3 check_setup.py || {
    echo ""
    echo "HATA: Kurulum kontrol başarısız!"
    echo "Lütfen eksik bağımlılıkları yükleyin:"
    echo "  pip install -r requirements.txt"
    exit 1
}

echo ""
echo "========================================"
echo "Servisler Başlatılıyor"
echo "========================================"
echo ""

# Backend'i arka planda başlat (127.0.0.1:8000)
echo "Backend başlatılıyor: http://127.0.0.1:8000"
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Kamera Servisi'ni arka planda başlat (127.0.0.1:8001)
echo "Kamera Servisi başlatılıyor: http://127.0.0.1:8001"
python3 -m uvicorn camera_service:app --host 127.0.0.1 --port 8001 &
CAMERA_PID=$!

# Frontend'i aç (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 2
    open "http://127.0.0.1:8000"
fi

echo ""
echo "========================================"
echo "Servisler Çalışıyor"
echo "========================================"
echo ""
echo "  Backend        -> http://127.0.0.1:8000"
echo "  Kamera Servisi -> http://127.0.0.1:8001"
echo ""
echo "Durdurmak için Ctrl+C tuşuna basın."
echo ""

# Her iki process tamamlanana kadar bekle
wait $BACKEND_PID $CAMERA_PID
