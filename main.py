"""
OrbitGuard — FastAPI uygulama giriş noktası
Backend API: host=127.0.0.1, port=8000
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from dependencies import celestrak_client
from middleware import LocalOnlyMiddleware
from routers import conjunction, groups, satellite, search

logger = logging.getLogger("orbitguard")

# ── Catalog categories ────────────────────────────────────────────────────────
CATALOG_CATEGORIES = [
    {"id": "turkish",  "search": None,            "norad_ids": [39522, 40984, 47949, 49382, 41875, 39030, 37791, 56224]},
    {"id": "stations", "search": "ISS",           "norad_ids": []},
    {"id": "starlink", "search": "STARLINK",      "norad_ids": []},
    {"id": "meteor",   "search": "METEOR",        "norad_ids": []},
    {"id": "debris",   "search": "COSMOS 2251",   "norad_ids": []},
    {"id": "debris",   "search": "IRIDIUM 33",    "norad_ids": []},
]

# ── Rate limiter ──────────────────────────────────────────────────────────────
# Tiered limits: global (all endpoints) + heavy (compute-intensive endpoints)
_GLOBAL_WINDOW  = 60    # seconds
_GLOBAL_MAX     = 300   # requests per window (localhost — generous)
_HEAVY_WINDOW   = 60
_HEAVY_MAX      = 30    # for /threats, /catalog/positions, /track

# Burst detection: if >40 requests in 5 seconds → temporary block
_BURST_WINDOW   = 5
_BURST_MAX      = 40
_BLOCK_DURATION = 15    # seconds to block after burst

_rate_store:  dict[str, list] = defaultdict(list)
_heavy_store: dict[str, list] = defaultdict(list)
_burst_store: dict[str, list] = defaultdict(list)
_blocked:     dict[str, float] = {}   # ip → unblock_time


def _check_rate_limit(ip: str, heavy: bool = False) -> None:
    now = time.time()

    # Check if IP is temporarily blocked
    if ip in _blocked:
        if now < _blocked[ip]:
            remaining = int(_blocked[ip] - now)
            logger.warning("Blocked IP attempted request: %s (%ds remaining)", ip, remaining)
            raise HTTPException(
                status_code=429,
                detail=f"Geçici olarak engellendi. {remaining}s sonra tekrar deneyin."
            )
        else:
            del _blocked[ip]

    # Burst detection
    burst_calls = [t for t in _burst_store[ip] if t > now - _BURST_WINDOW]
    burst_calls.append(now)
    _burst_store[ip] = burst_calls
    if len(burst_calls) > _BURST_MAX:
        _blocked[ip] = now + _BLOCK_DURATION
        logger.warning("Burst detected from %s — blocking for %ds", ip, _BLOCK_DURATION)
        raise HTTPException(
            status_code=429,
            detail=f"Çok hızlı istek. {_BLOCK_DURATION}s engellendi."
        )

    # Global rate limit
    global_calls = [t for t in _rate_store[ip] if t > now - _GLOBAL_WINDOW]
    global_calls.append(now)
    _rate_store[ip] = global_calls
    if len(global_calls) > _GLOBAL_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"İstek limiti aşıldı. {_GLOBAL_WINDOW}s içinde en fazla {_GLOBAL_MAX} istek."
        )

    # Heavy endpoint limit
    if heavy:
        heavy_calls = [t for t in _heavy_store[ip] if t > now - _HEAVY_WINDOW]
        heavy_calls.append(now)
        _heavy_store[ip] = heavy_calls
        if len(heavy_calls) > _HEAVY_MAX:
            raise HTTPException(
                status_code=429,
                detail=f"Hesaplama limiti aşıldı. {_HEAVY_WINDOW}s içinde en fazla {_HEAVY_MAX} ağır istek."
            )


# ── Global rate limit middleware ──────────────────────────────────────────────
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies global rate limiting to all API requests."""

    # Static files and health check are exempt
    _EXEMPT_PREFIXES = ("/frontend/", "/static/")
    _EXEMPT_PATHS    = ("/", "/health")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip static files and root
        if any(path.startswith(p) for p in self._EXEMPT_PREFIXES):
            return await call_next(request)
        if path in self._EXEMPT_PATHS:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"

        # Heavy endpoints get stricter limits
        heavy = any(path.startswith(p) for p in (
            "/api/threats/",
            "/api/catalog/positions",
            "/api/catalog",
            "/api/conjunction/",
        )) or path.endswith("/track")

        try:
            _check_rate_limit(ip, heavy=heavy)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers={"Retry-After": "30"},
            )

        response = await call_next(request)
        return response


# ── Allowed NORAD ID range ────────────────────────────────────────────────────
_NORAD_MIN = 1
_NORAD_MAX = 99999

app = FastAPI(title="OrbitGuard", version="1.0")

# IP erişim kontrolü — sadece localhost
app.add_middleware(LocalOnlyMiddleware)
# Rate limiting — tüm API isteklerine uygulanır
app.add_middleware(RateLimitMiddleware)


@app.on_event("startup")
async def _start_cleanup():
    """Periodically clean up stale rate limit entries."""
    import asyncio

    async def cleanup():
        while True:
            await asyncio.sleep(300)  # every 5 minutes
            now = time.time()
            for store in (_rate_store, _heavy_store, _burst_store):
                stale = [ip for ip, calls in store.items()
                         if not calls or max(calls) < now - 120]
                for ip in stale:
                    del store[ip]
            stale_blocked = [ip for ip, t in _blocked.items() if t < now]
            for ip in stale_blocked:
                del _blocked[ip]

    asyncio.create_task(cleanup())

# Router'ları dahil et
app.include_router(search.router)
app.include_router(satellite.router)
app.include_router(groups.router)
app.include_router(conjunction.router)

# Frontend dosyasını serve et
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")


@app.get("/")
async def root():
    frontend_file = Path(__file__).parent / "frontend" / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file, media_type="text/html")
    return {"status": "ok", "version": "1.0"}


@app.get("/health")
async def health():
    celestrak_ok = await celestrak_client.health_check()
    return {
        "status": "ok",
        "celestrak_ok": celestrak_ok,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/catalog")
async def get_catalog():
    """
    Returns all tracked objects grouped by category.
    Each item: {norad_id, name, line1, line2, category}
    """
    results = []

    for cat in CATALOG_CATEGORIES:
        cat_id = cat["id"]

        # Fetch individual NORAD IDs (Turkish satellites)
        for norad_id in cat["norad_ids"]:
            try:
                data = await celestrak_client.fetch_by_catnr(norad_id)
                if data:
                    rec = data[0]
                    results.append({
                        "norad_id": rec.get("satelliteId") or norad_id,
                        "name": rec.get("name", ""),
                        "line1": rec.get("line1", ""),
                        "line2": rec.get("line2", ""),
                        "category": cat_id,
                    })
            except Exception:
                pass

        # Fetch by search term (stations, starlink, meteor, debris)
        if cat["search"]:
            try:
                data = await celestrak_client.fetch_by_name(cat["search"])
                for rec in data[:100]:  # cap per category
                    results.append({
                        "norad_id": rec.get("satelliteId"),
                        "name": rec.get("name", ""),
                        "line1": rec.get("line1", ""),
                        "line2": rec.get("line2", ""),
                        "category": cat_id,
                    })
            except Exception:
                pass

    return results


@app.get("/api/catalog/positions")
async def get_catalog_positions():
    """
    Returns current geodetic positions for all catalog objects in one shot.
    Each item: {norad_id, name, category, lat, lon, alt_km}
    SGP4 propagation done server-side so the frontend doesn't need per-object calls.
    """
    from sgp4_engine import SGP4Engine, PropagationError, CoordinateError
    engine = SGP4Engine()
    now = datetime.now(timezone.utc)

    catalog = await get_catalog()
    positions = []

    for obj in catalog:
        line1 = obj.get("line1", "")
        line2 = obj.get("line2", "")
        if not line1 or not line2:
            continue
        try:
            result = engine.propagate(line1, line2, now)
            geo = engine.eci_to_geodetic(result["eci"]["x"], result["eci"]["y"], result["eci"]["z"], now)
            positions.append({
                "norad_id": obj["norad_id"],
                "name": obj["name"],
                "category": obj["category"],
                "lat": round(geo["lat"], 4),
                "lon": round(geo["lon"], 4),
                "alt_km": round(geo["alt_km"], 1),
            })
        except (ValueError, PropagationError, CoordinateError, Exception):
            pass

    return positions


@app.get("/api/threats/{norad_id}")
async def get_threats(
    request: Request,
    norad_id: int,
    days: int = Query(default=7, ge=1, le=14),
):
    """
    Find all catalog objects that could come within 50 km of the given satellite.
    Uses the enhanced ConjunctionEngine with 2-phase scan + collision probability.
    Returns sorted by danger_score descending. Top 50 results.
    """
    # Input validation
    if not (_NORAD_MIN <= norad_id <= _NORAD_MAX):
        raise HTTPException(status_code=400, detail=f"Geçersiz NORAD ID: {norad_id}")

    from conjunction import ConjunctionEngine

    # Fetch target satellite TLE
    target_data = await celestrak_client.fetch_by_catnr(norad_id)
    if not target_data:
        raise HTTPException(status_code=404, detail="Uydu bulunamadı")

    target = target_data[0]
    t_line1, t_line2 = target.get("line1", ""), target.get("line2", "")
    if not t_line1 or not t_line2:
        raise HTTPException(status_code=422, detail="TLE verisi yok")

    target_tle = {
        "norad_id": norad_id,
        "name": target.get("name", ""),
        "tle_line1": t_line1,
        "tle_line2": t_line2,
        "category": "satellite",
    }

    catalog_raw = await get_catalog()
    engine = ConjunctionEngine()
    threats = []

    for obj in catalog_raw:
        if obj["norad_id"] == norad_id:
            continue
        line1, line2 = obj.get("line1", ""), obj.get("line2", "")
        if not line1 or not line2:
            continue

        obj_tle = {
            "norad_id": obj["norad_id"],
            "name": obj["name"],
            "tle_line1": line1,
            "tle_line2": line2,
            "category": obj.get("category", "other"),
        }

        if engine._quick_filter(target_tle, obj_tle):
            continue

        events = engine.analyze_pair(target_tle, obj_tle, days=days)
        for ev in events:
            threats.append({
                "norad_id":           obj["norad_id"],
                "name":               obj["name"],
                "category":           obj.get("category", "other"),
                "miss_distance_km":   ev["miss_distance_km"],
                "rel_speed_km_s":     ev.get("rel_speed_km_s", 0),
                "approach_angle_deg": ev.get("approach_angle_deg", 0),
                "collision_prob":     ev.get("collision_prob", 0),
                "danger_score":       ev.get("danger_score", 0),
                "impact_energy_kj":   ev.get("impact_energy_kj", 0),
                "risk_level":         ev["risk_level"],
                "tca":                ev["tca"],
            })

    # Deduplicate — keep worst event per object
    seen: dict = {}
    for t in threats:
        nid = t["norad_id"]
        if nid not in seen or t["danger_score"] > seen[nid]["danger_score"]:
            seen[nid] = t

    return sorted(seen.values(), key=lambda x: x["danger_score"], reverse=True)[:50]



@app.get("/api/satellite/{norad_id}/track")
async def get_satellite_track(norad_id: int, minutes: int = 90, step: int = 60):
    """
    Returns the ground track (lat/lon/alt) for the next `minutes` minutes
    at `step` second intervals. Used to draw the real orbital path.
    Max 180 minutes, min step 30s.
    """
    from fastapi import HTTPException
    from sgp4_engine import SGP4Engine, PropagationError, CoordinateError
    import datetime as dt_mod

    minutes = min(max(minutes, 5), 180)
    step    = max(step, 30)

    data = await celestrak_client.fetch_by_catnr(norad_id)
    if not data:
        raise HTTPException(status_code=404, detail="Uydu bulunamadı")

    rec = data[0]
    line1, line2 = rec.get("line1",""), rec.get("line2","")
    if not line1 or not line2:
        raise HTTPException(status_code=422, detail="TLE verisi yok")

    engine = SGP4Engine()
    now = datetime.now(timezone.utc)
    points = []

    for s in range(0, minutes * 60 + 1, step):
        t = now + dt_mod.timedelta(seconds=s)
        try:
            r = engine.propagate(line1, line2, t)
            geo = engine.eci_to_geodetic(r["eci"]["x"], r["eci"]["y"], r["eci"]["z"], t)
            points.append({
                "lat":    round(geo["lat"], 4),
                "lon":    round(geo["lon"], 4),
                "alt_km": round(geo["alt_km"], 1),
                "t":      s,
            })
        except (PropagationError, CoordinateError, Exception):
            continue

    return points
async def camera_status():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://127.0.0.1:8001/camera/status")
            return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException, Exception):
        return JSONResponse(
            status_code=503,
            content={"detail": "Camera service unavailable"},
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
