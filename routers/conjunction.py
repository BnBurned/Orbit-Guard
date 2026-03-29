"""
Konjunksiyon router'ı — OrbitGuard
Gereksinimler: 9.1, 9.2, 9.3, 9.4, 9.5
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query

from celestrak_client import CelesTrakClient
from conjunction import ConjunctionEngine, TURKISH_SATELLITES
from dependencies import celestrak_client as _default_client

router = APIRouter(prefix="/api/conjunction", tags=["conjunction"])

_conjunction_engine = ConjunctionEngine()

# Debris grubu — Cosmos 1408 parçalanma enkazı
_DEBRIS_GROUP = "cosmos-1408-debris"


def get_celestrak_client() -> CelesTrakClient:
    """FastAPI dependency: paylaşılan CelesTrakClient singleton'ını döndürür."""
    return _default_client


def _extract_tle_record(data: Any, norad_id: int) -> dict | None:
    """
    CelesTrak yanıtından TLE kaydını çıkarır.
    Liste ise ilk elemanı, dict ise kendisini döndürür.
    Bulunamazsa None döndürür.
    """
    if isinstance(data, list):
        if len(data) == 0:
            return None
        return data[0]
    if isinstance(data, dict):
        return data
    return None


def _record_to_tle_dict(record: dict, norad_id: int) -> dict | None:
    """
    Convert a normalized TLE API record to the format expected by ConjunctionEngine.
    Returns None if TLE lines are missing.
    """
    tle_line1 = str(record.get("TLE_LINE1", record.get("line1", ""))).strip()
    tle_line2 = str(record.get("TLE_LINE2", record.get("line2", ""))).strip()
    if not tle_line1 or not tle_line2:
        return None
    return {
        "norad_id": int(record.get("NORAD_CAT_ID", record.get("satelliteId", norad_id)) or norad_id),
        "name": str(record.get("OBJECT_NAME", record.get("name", ""))).strip(),
        "tle_line1": tle_line1,
        "tle_line2": tle_line2,
    }


def _group_records_to_tle_list(data: Any) -> List[dict]:
    """Convert a list of normalized TLE API records to ConjunctionEngine format."""
    if not isinstance(data, list):
        return []
    result = []
    for record in data:
        if not isinstance(record, dict):
            continue
        tle_line1 = str(record.get("TLE_LINE1", record.get("line1", ""))).strip()
        tle_line2 = str(record.get("TLE_LINE2", record.get("line2", ""))).strip()
        if not tle_line1 or not tle_line2:
            continue
        norad_id = int(record.get("NORAD_CAT_ID", record.get("satelliteId", 0)) or 0)
        result.append({
            "norad_id": norad_id,
            "name": str(record.get("OBJECT_NAME", record.get("name", ""))).strip(),
            "tle_line1": tle_line1,
            "tle_line2": tle_line2,
        })
    return result


@router.get("/turkish-satellites")
async def get_turkish_satellites_conjunction(
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> List[dict]:
    """
    GET /api/conjunction/turkish-satellites
    6 Türk uydusu ile debris listesi arasındaki konjunksiyon olaylarını döndürür.
    Propagasyon: 7 gün, 60 saniyelik adımlar.
    Gereksinim 9.1, 9.2, 9.3
    """
    # Fetch debris TLEs from all major debris clouds
    try:
        debris_data = await client.fetch_debris_catalog()
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"TLE API erişilemez: {exc}") from exc

    all_tles = _group_records_to_tle_list(debris_data)

    # 6 Türk uydusunun TLE'lerini çek ve listeye ekle
    for sat in TURKISH_SATELLITES:
        try:
            sat_data = await client.fetch_by_catnr(sat["norad_id"])
        except (TimeoutError, ConnectionError):
            # Tek bir uydu alınamazsa atla, diğerlerine devam et
            continue

        record = _extract_tle_record(sat_data, sat["norad_id"])
        if record is None:
            continue

        tle_dict = _record_to_tle_dict(record, sat["norad_id"])
        if tle_dict is None:
            continue

        # Zaten listede yoksa ekle
        if not any(t["norad_id"] == tle_dict["norad_id"] for t in all_tles):
            all_tles.append(tle_dict)

    events = _conjunction_engine.analyze_turkish_satellites(all_tles)
    return events


@router.get("/pair")
async def get_pair_conjunction(
    sat1: int = Query(..., description="Birinci uydunun NORAD_ID'si"),
    sat2: int = Query(..., description="İkinci uydunun NORAD_ID'si"),
    days: int = Query(7, ge=1, le=30, description="Analiz süresi (gün)"),
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> List[dict]:
    """
    GET /api/conjunction/pair?sat1=<norad1>&sat2=<norad2>&days=7
    İki uydu arasındaki konjunksiyon analizini döndürür.
    Bulunamayan NORAD_ID → 404.
    Gereksinim 9.4, 9.5
    """
    # İlk uyduyu çek
    try:
        data1 = await client.fetch_by_catnr(sat1)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"TLE API erişilemez: {exc}") from exc

    record1 = _extract_tle_record(data1, sat1)
    if record1 is None:
        raise HTTPException(status_code=404, detail=f"Uydu bulunamadı: NORAD_ID={sat1}")

    tle1 = _record_to_tle_dict(record1, sat1)
    if tle1 is None:
        raise HTTPException(status_code=404, detail=f"TLE verisi bulunamadı: NORAD_ID={sat1}")

    # İkinci uyduyu çek
    try:
        data2 = await client.fetch_by_catnr(sat2)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"TLE API erişilemez: {exc}") from exc

    record2 = _extract_tle_record(data2, sat2)
    if record2 is None:
        raise HTTPException(status_code=404, detail=f"Uydu bulunamadı: NORAD_ID={sat2}")

    tle2 = _record_to_tle_dict(record2, sat2)
    if tle2 is None:
        raise HTTPException(status_code=404, detail=f"TLE verisi bulunamadı: NORAD_ID={sat2}")

    events = _conjunction_engine.analyze_pair(tle1, tle2, days=days)
    return events
