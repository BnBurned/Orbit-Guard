"""
Uydu arama router'ı — OrbitGuard
Gereksinimler: 5.1, 5.2, 5.3, 5.4
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query

from celestrak_client import CelesTrakClient
from dependencies import celestrak_client as _default_client

router = APIRouter(prefix="/api/search", tags=["search"])


def get_celestrak_client() -> CelesTrakClient:
    """FastAPI dependency: paylaşılan CelesTrakClient singleton'ını döndürür."""
    return _default_client


@router.get("/name")
async def search_by_name(
    q: str = Query(default=None, description="Aranacak uydu ismi"),
    format: str = Query(default="json"),
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> List[Any]:
    """
    GET /api/search/name?q=<sorgu>&format=json
    Adında sorgu dizesini içeren tüm uyduların TLE verilerini döndürür.
    Gereksinim 5.1, 5.3, 5.4
    """
    if q is None or q == "":
        raise HTTPException(status_code=400, detail="'q' parametresi eksik veya geçersiz.")

    try:
        data = await client.fetch_by_name(q)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"CelesTrak erişilemez: {exc}") from exc

    if data is None:
        return []
    if isinstance(data, list):
        return data
    # Tek nesne döndüyse listeye sar
    return [data]


@router.get("/catnr")
async def search_by_catnr(
    id: str = Query(default=None, description="NORAD katalog numarası"),
    format: str = Query(default="json"),
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> List[Any]:
    """
    GET /api/search/catnr?id=<norad_id>&format=json
    Belirtilen NORAD_ID'ye sahip uydunun TLE verisini döndürür.
    Gereksinim 5.2, 5.3, 5.4
    """
    if id is None or not str(id).strip():
        raise HTTPException(status_code=400, detail="'id' parametresi eksik veya geçersiz.")

    try:
        norad_id = int(id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="'id' parametresi geçerli bir tamsayı olmalıdır.")

    if norad_id <= 0:
        raise HTTPException(status_code=400, detail="'id' parametresi pozitif bir tamsayı olmalıdır.")

    try:
        data = await client.fetch_by_catnr(norad_id)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"CelesTrak erişilemez: {exc}") from exc

    if data is None:
        return []
    if isinstance(data, list):
        return data
    return [data]
