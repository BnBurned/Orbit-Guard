"""
Grup sorgu router'ı — OrbitGuard
Gereksinimler: 7.1, 7.2, 7.3
"""

from fastapi import APIRouter, Depends, HTTPException

from celestrak_client import CelesTrakClient
from dependencies import celestrak_client as _default_client

router = APIRouter(prefix="/api/groups", tags=["groups"])

SUPPORTED_GROUPS = {
    "active", "stations", "visual", "weather", "noaa", "goes", "resource",
    "sarsat", "dmc", "tdrss", "argos", "planet", "spire", "geo", "intelsat",
    "ses", "iridium", "iridium-NEXT", "starlink", "oneweb", "orbcomm",
    "globalstar", "swarm", "amateur", "x-comm", "other-comm", "satnogs",
    "gorizont", "raduga", "molniya", "cosmos-1408-debris", "fengyun-1c-debris",
    "iridium-33-debris", "cosmos-2251-debris",
}


def get_celestrak_client() -> CelesTrakClient:
    """FastAPI dependency: paylaşılan CelesTrakClient singleton'ını döndürür."""
    return _default_client


@router.get("/{group}/count")
async def get_group_count(
    group: str,
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> dict:
    """
    GET /api/groups/{group}/count
    Gruptaki uydu sayısını döndürür: {"group": str, "count": int}.
    Gereksinim 7.2, 7.3
    """
    if group not in SUPPORTED_GROUPS:
        raise HTTPException(status_code=404, detail=f"Desteklenmeyen grup: {group}")

    try:
        data = await client.fetch_group(group, limit=500)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"CelesTrak erişilemez: {exc}") from exc

    count = len(data) if isinstance(data, list) else 0
    return {"group": group, "count": count}


@router.get("/{group}")
async def get_group(
    group: str,
    format: str = "json",
    limit: int = 500,
    client: CelesTrakClient = Depends(get_celestrak_client),
) -> list:
    """
    GET /api/groups/{group}?format=json&limit=500
    Grup TLE listesini en fazla 500 kayıtla döndürür.
    Gereksinim 7.1, 7.3
    """
    if group not in SUPPORTED_GROUPS:
        raise HTTPException(status_code=404, detail=f"Desteklenmeyen grup: {group}")

    # Limit 500 ile sınırla
    effective_limit = min(limit, 500)

    try:
        data = await client.fetch_group(group, limit=effective_limit)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"CelesTrak erişilemez: {exc}") from exc

    if not isinstance(data, list):
        return []

    return data[:effective_limit]
