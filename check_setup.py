#!/usr/bin/env python3
"""
OrbitGuard Kurulum Kontrol Betiği
Tüm bağımlılıkları ve yapılandırmayı doğrular.
"""

import sys
from pathlib import Path

def check_imports():
    """Tüm gerekli modülleri kontrol et."""
    print("📦 Bağımlılıklar kontrol ediliyor...")
    
    required = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("httpx", "HTTPX"),
        ("sgp4", "SGP4"),
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("hypothesis", "Hypothesis"),
        ("pytest", "Pytest"),
    ]
    
    missing = []
    for module, name in required:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} — EKSIK")
            missing.append(module)
    
    return len(missing) == 0, missing

def check_files():
    """Gerekli dosyaları kontrol et."""
    print("\n📁 Dosyalar kontrol ediliyor...")
    
    required_files = [
        "main.py",
        "camera_service.py",
        "middleware.py",
        "dependencies.py",
        "celestrak_client.py",
        "sgp4_engine.py",
        "conjunction.py",
        "requirements.txt",
        "frontend/index.html",
        "routers/__init__.py",
        "routers/search.py",
        "routers/satellite.py",
        "routers/groups.py",
        "routers/conjunction.py",
    ]
    
    missing = []
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} — EKSIK")
            missing.append(file)
    
    return len(missing) == 0, missing

def check_ports():
    """Port kullanılabilirliğini kontrol et."""
    print("\n🔌 Portlar kontrol ediliyor...")
    
    import socket
    
    ports = [8000, 8001]
    available = True
    
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        
        if result == 0:
            print(f"  ⚠ Port {port} — KULLANIMDA (başka bir servis çalışıyor)")
            available = False
        else:
            print(f"  ✓ Port {port} — Kullanılabilir")
    
    return available

def main():
    print("=" * 50)
    print("OrbitGuard Kurulum Kontrol")
    print("=" * 50)
    
    imports_ok, missing_imports = check_imports()
    files_ok, missing_files = check_files()
    ports_ok = check_ports()
    
    print("\n" + "=" * 50)
    print("ÖZET")
    print("=" * 50)
    
    if imports_ok and files_ok and ports_ok:
        print("✓ Tüm kontroller başarılı!")
        print("\nOrbitGuard'ı başlatmak için:")
        print("  Windows: run.bat")
        print("  Linux/macOS: ./run.sh")
        return 0
    else:
        print("✗ Bazı sorunlar bulundu:")
        if not imports_ok:
            print(f"\n  Eksik bağımlılıklar: {', '.join(missing_imports)}")
            print("  Çözüm: pip install -r requirements.txt")
        if not files_ok:
            print(f"\n  Eksik dosyalar: {', '.join(missing_files)}")
        if not ports_ok:
            print("\n  Çözüm: Diğer uygulamaları kapatın veya portları değiştirin")
        return 1

if __name__ == "__main__":
    sys.exit(main())
