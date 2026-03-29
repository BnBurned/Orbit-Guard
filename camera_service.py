"""
Kamera Servisi — OrbitGuard
Bağımsız FastAPI uygulaması, port 8001
"""
import asyncio
import threading
from datetime import datetime, timezone
from typing import Generator

import cv2
import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

from middleware import LocalOnlyMiddleware

app = FastAPI(title="OrbitGuard Camera Service")
app.add_middleware(LocalOnlyMiddleware)

# ---------------------------------------------------------------------------
# Durum
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_cap: cv2.VideoCapture | None = None
_mog2: cv2.BackgroundSubtractorMOG2 | None = None
_active: bool = False
_detections: list[dict] = []  # max 100 giriş

OBSERVER = {"name": "Ankara", "lat": 39.9, "lon": 32.8, "alt_m": 938}


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _process_frame(frame: np.ndarray) -> np.ndarray:
    """MOG2 ile hareketi işle, konturları çiz ve algılamaları kaydet."""
    global _detections

    fg_mask = _mog2.apply(frame)

    # Gürültüyü azalt
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        detection = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contour_area": float(area),
            "bbox": [x, y, w, h],
        }
        with _lock:
            _detections.append(detection)
            if len(_detections) > 100:
                _detections = _detections[-100:]

    return frame


def _mjpeg_generator() -> Generator[bytes, None, None]:
    """Aktif olduğu sürece MJPEG kareleri üret."""
    while True:
        with _lock:
            active = _active
            cap = _cap

        if not active or cap is None:
            # Kamera kapalıyken siyah kare gönder
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            _, buf = cv2.imencode(".jpg", blank)
            frame_bytes = buf.tobytes()
        else:
            ret, frame = cap.read()
            if not ret:
                break
            frame = _process_frame(frame)
            _, buf = cv2.imencode(".jpg", frame)
            frame_bytes = buf.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


# ---------------------------------------------------------------------------
# Endpoint'ler
# ---------------------------------------------------------------------------

@app.post("/camera/start")
async def camera_start():
    global _cap, _mog2, _active

    with _lock:
        if _active:
            return JSONResponse({"status": "already_active"})

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return JSONResponse({"detail": "Webcam unavailable"}, status_code=503)

        _cap = cap
        _mog2 = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=True
        )
        _active = True

    return JSONResponse({"status": "started"})


@app.post("/camera/stop")
async def camera_stop():
    global _cap, _mog2, _active

    with _lock:
        if _cap is not None:
            _cap.release()
            _cap = None
        _mog2 = None
        _active = False

    return JSONResponse({"status": "stopped"})


@app.get("/camera/stream")
async def camera_stream():
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/camera/status")
async def camera_status():
    with _lock:
        active = _active
        count = len(_detections)

    return JSONResponse({
        "active": active,
        "observer": OBSERVER,
        "detections_count": count,
    })


@app.get("/camera/detections")
async def camera_detections():
    with _lock:
        result = list(_detections)
    return JSONResponse(result)


# ---------------------------------------------------------------------------
# Giriş noktası
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
