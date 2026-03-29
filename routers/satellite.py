"""
Tekil uydu router'ı — OrbitGuard
Gereksinimler: 6.1, 6.2, 6.3, 6.4
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from celestrak_client import CelesTrakClient
from dependencies import celestrak_client as _default_client
from sgp4_engine import SGP4Engine, PropagationError, CoordinateError

router = APIRouter(prefix="/api/satellite", tags=["satellite"])

_sgp4 = SGP4Engine()


def get_celestrak_client() -> CelesTrakClient:
    """FastAPI dependency: paylaşılan CelesTrakClient singleton'ını döndürür."""
    return _default_client


def _get_satellite_record(data: Any) -> dict:
    """
    CelesTrak yanıtından ilk uydu kaydını çıkarır.
    Bulunamazsa None döndürür.
    """
    if isinstance(data, list):
        if len(data) == 0:
            return None
        return data[0]
    if isinstance(data, dict):
        return data
    return None


def _parse_satellite_info(record: dict) -> dict:
    """
    Build satellite info dict from a normalized TLE API record.
    Orbital elements (inclination, eccentricity, altitude, period) are
    derived from SGP4 propagation — NOT parsed from TLE fields manually.
    Requirement 6.1
    """
    tle_line1 = str(record.get("TLE_LINE1", record.get("line1", ""))).strip()
    tle_line2 = str(record.get("TLE_LINE2", record.get("line2", ""))).strip()
    name = str(record.get("OBJECT_NAME", record.get("name", ""))).strip()
    norad_id = int(record.get("NORAD_CAT_ID", record.get("satelliteId", 0)) or 0)
    epoch_raw = record.get("EPOCH", record.get("date", ""))

    # Epoch — ISO 8601
    try:
        epoch_dt = datetime.fromisoformat(str(epoch_raw).replace("Z", "+00:00"))
        epoch_str = epoch_dt.isoformat()
    except (ValueError, TypeError):
        epoch_str = str(epoch_raw)

    # Derive orbital elements from SGP4
    inclination = 0.0
    eccentricity = 0.0
    altitude_km = 0.0
    period_min = 0.0
    orbit_type = "UNKNOWN"

    if tle_line1 and tle_line2:
        try:
            elements = _sgp4.orbital_elements(tle_line1, tle_line2)
            inclination = elements.get("inclination_deg", 0.0)
            eccentricity = elements.get("eccentricity", 0.0)
            period_min = elements.get("period_min", 0.0)
            perigee = elements.get("perigee_km", 0.0)
            apogee = elements.get("apogee_km", 0.0)
            altitude_km = (perigee + apogee) / 2.0
            mean_alt = altitude_km
            if mean_alt > 35000:
                orbit_type = "GEO"
            elif mean_alt < 2000:
                orbit_type = "LEO"
            elif mean_alt < 35000:
                orbit_type = "MEO"
            else:
                orbit_type = "OTHER"
        except Exception:
            pass

    return {
        "name": name,
        "norad_id": norad_id,
        "epoch": epoch_str,
        "inclination": round(inclination, 4),
        "eccentricity": round(eccentricity, 7),
        "altitude_km": round(altitude_km, 3),
        "period_min": round(period_min, 6),
        "orbit_type": orbit_type,
        "tle_line1": tle_line1,
        "tle_line2": tle_line2,
    }


@router.get("/{catnr}")
async def get_satellite(
    catnr: int,
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> dict:
    """
    GET /api/satellite/{catnr}
    Uydu bilgisini döndürür: name, norad_id, epoch, inclination, eccentricity,
    altitude_km, period_min, orbit_type, tle_line1, tle_line2.
    Gereksinim 6.1, 6.4
    """
    try:
        data = await client.fetch_by_catnr(catnr)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"CelesTrak erişilemez: {exc}") from exc

    record = _get_satellite_record(data)
    if record is None:
        raise HTTPException(status_code=404, detail="Uydu bulunamadı.")

    return _parse_satellite_info(record)


@router.get("/{catnr}/position")
async def get_satellite_position(
    catnr: int,
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> dict:
    """
    GET /api/satellite/{catnr}/position
    Anlık ECI koordinatları, geodetik konum ve hız vektörünü döndürür.
    Gereksinim 6.2, 6.4
    """
    try:
        data = await client.fetch_by_catnr(catnr)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"CelesTrak erişilemez: {exc}") from exc

    record = _get_satellite_record(data)
    if record is None:
        raise HTTPException(status_code=404, detail="Uydu bulunamadı.")

    tle_line1 = str(record.get("TLE_LINE1", record.get("line1", ""))).strip()
    tle_line2 = str(record.get("TLE_LINE2", record.get("line2", ""))).strip()

    if not tle_line1 or not tle_line2:
        raise HTTPException(status_code=422, detail="TLE verisi mevcut değil.")

    now = datetime.now(timezone.utc)

    try:
        result = _sgp4.propagate(tle_line1, tle_line2, now)
        geodetic = _sgp4.eci_to_geodetic(
            result["eci"]["x"],
            result["eci"]["y"],
            result["eci"]["z"],
            now,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Geçersiz TLE: {exc}") from exc
    except PropagationError as exc:
        raise HTTPException(status_code=422, detail=f"Propagasyon hatası: {exc}") from exc
    except CoordinateError as exc:
        raise HTTPException(status_code=422, detail=f"Koordinat dönüşüm hatası: {exc}") from exc

    return {
        "eci": result["eci"],
        "geodetic": geodetic,
        "velocity": result["velocity"],
    }


@router.get("/{catnr}/orbital")
async def get_satellite_orbital(
    catnr: int,
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> dict:
    """
    GET /api/satellite/{catnr}/orbital
    Yörünge parametrelerini döndürür: perigee_km, apogee_km, period_min,
    inclination_deg, orbit_type.
    Gereksinim 6.3, 6.4
    """
    try:
        data = await client.fetch_by_catnr(catnr)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"CelesTrak erişilemez: {exc}") from exc

    record = _get_satellite_record(data)
    if record is None:
        raise HTTPException(status_code=404, detail="Uydu bulunamadı.")

    tle_line1 = str(record.get("TLE_LINE1", record.get("line1", ""))).strip()
    tle_line2 = str(record.get("TLE_LINE2", record.get("line2", ""))).strip()

    if not tle_line1 or not tle_line2:
        raise HTTPException(status_code=422, detail="TLE verisi mevcut değil.")

    try:
        elements = _sgp4.orbital_elements(tle_line1, tle_line2)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Geçersiz TLE: {exc}") from exc

    return elements
