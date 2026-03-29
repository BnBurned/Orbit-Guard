#!/usr/bin/env bash
# OrbitGuard Tanı Betiği (Linux/macOS)
# Sorunları tespit etmek için çalıştırın

echo ""
echo "========================================"
echo "OrbitGuard Tanı Betiği"
echo "========================================"
echo ""

# Python kontrolü
echo "[1/5] Python kontrolü..."
if ! command -v python3 &> /dev/null; then
    echo "   ✗ Python3 yüklü değil!"
    echo "   Çözüm: apt-get install python3 (Linux) veya brew install python3 (macOS)"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    echo "   ✓ $PYTHON_VERSION"
fi

# Bağımlılıklar kontrolü
echo ""
echo "[2/5] Bağımlılıklar kontrolü..."
python3 check_setup.py
if [ $? -ne 0 ]; then
    echo ""
    echo "   ✗ Bağımlılıklar eksik!"
    echo "   Çözüm: pip install -r requirements.txt"
    exit 1
fi

# Port kontrolü
echo ""
echo "[3/5] Port kontrolü..."

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠ Port 8000 kullanımda"
    echo "   Çözüm: kill -9 \$(lsof -t -i:8000)"
else
    echo "   ✓ Port 8000 kullanılabilir"
fi

if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠ Port 8001 kullanımda"
    echo "   Çözüm: kill -9 \$(lsof -t -i:8001)"
else
    echo "   ✓ Port 8001 kullanılabilir"
fi

# Dosya yapısı kontrolü
echo ""
echo "[4/5] Dosya yapısı kontrolü..."

if [ -f "main.py" ]; then
    echo "   ✓ main.py"
else
    echo "   ✗ main.py eksik"
    exit 1
fi

if [ -f "camera_service.py" ]; then
    echo "   ✓ camera_service.py"
else
    echo "   ✗ camera_service.py eksik"
    exit 1
fi

if [ -f "frontend/index.html" ]; then
    echo "   ✓ frontend/index.html"
else
    echo "   ✗ frontend/index.html eksik"
    exit 1
fi

# Webcam kontrolü
echo ""
echo "[5/5] Webcam kontrolü..."
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('   ✓ Webcam kullanılabilir' if cap.isOpened() else '   ⚠ Webcam bulunamadı'); cap.release()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ⚠ Webcam kontrol edilemedi"
fi

echo ""
echo "========================================"
echo "Tanı Tamamlandı"
echo "========================================"
echo ""
echo "Tüm kontroller başarılı!"
echo "OrbitGuard'ı başlatmak için: ./run.sh"
echo ""
