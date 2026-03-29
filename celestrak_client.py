"""
TLE API client for OrbitGuard — tle.ivanstanojevic.me
Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5

Base URL: https://tle.ivanstanojevic.me/api/tle
- GET /api/tle/{norad_id}          → single satellite
- GET /api/tle?search=<query>      → search by name (paginated)
- GET /api/tle?page=N&page-size=100 → paginate all
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://tle.ivanstanojevic.me/api/tle/"
USER_AGENT = "OrbitGuard/1.0"
TIMEOUT_SECONDS = 90
GROUP_TTL = 900   # 15 minutes
SINGLE_TTL = 300  # 5 minutes

# Debris search queries — covers major debris clouds
DEBRIS_SEARCHES = [
    "COSMOS DEB",
    "IRIDIUM DEB",
    "FENGYUN DEB",
    "BREEZE-M DEB",
]

# Turkish satellite NORAD IDs
TURKISH_NORAD_IDS = [39522, 40984, 47949, 49382, 41875, 39030, 37791, 56224]


@dataclass
class CacheEntry:
    data: Any
    fetched_at: float
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        return time.time() - self.fetched_at > self.ttl_seconds


def _normalize(item: dict) -> dict:
    """
    Normalize a TLE API response item into a consistent internal dict.
    Maps new API fields → internal field names used throughout the app.
    """
    return {
        # New API fields
        "satelliteId": item.get("satelliteId"),
        "name": item.get("name", ""),
        "date": item.get("date", ""),
        "line1": item.get("line1", ""),
        "line2": item.get("line2", ""),
        # Aliases for backward compat with routers
        "NORAD_CAT_ID": item.get("satelliteId"),
        "OBJECT_NAME": item.get("name", ""),
        "TLE_LINE1": item.get("line1", ""),
        "TLE_LINE2": item.get("line2", ""),
        "EPOCH": item.get("date", ""),
    }


class CelesTrakClient:
    """
    Async HTTP client for tle.ivanstanojevic.me TLE API.
    Drop-in replacement for the old CelesTrak client.
    """

    def __init__(self) -> None:
        self._semaphore = asyncio.Semaphore(10)
        self._cache: dict[str, CacheEntry] = {}
        self._headers = {"User-Agent": USER_AGENT}

    # ------------------------------------------------------------------ #
    # Internal HTTP                                                         #
    # ------------------------------------------------------------------ #

    async def _get_json(self, url: str, params: dict | None = None) -> Any:
        """GET request with semaphore, timeout, and retry."""
        async with self._semaphore:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(TIMEOUT_SECONDS),
                        headers=self._headers,
                        follow_redirects=True,
                    ) as client:
                        response = await client.get(url, params=params)
                        response.raise_for_status()
                        return response.json()
                except httpx.TimeoutException as exc:
                    logger.error("TLE API timeout (attempt %d/%d): %s", attempt + 1, max_retries, exc)
                    if attempt == max_retries - 1:
                        raise TimeoutError(f"TLE API did not respond within {TIMEOUT_SECONDS}s.") from exc
                    await asyncio.sleep(2 ** attempt)
                except httpx.ConnectError as exc:
                    logger.error("TLE API connection error (attempt %d/%d): %s", attempt + 1, max_retries, exc)
                    if attempt == max_retries - 1:
                        raise ConnectionError(f"Cannot connect to TLE API: {exc}") from exc
                    await asyncio.sleep(2 ** attempt)
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 404:
                        return None  # Caller handles not-found
                    logger.error("TLE API HTTP error: %s", exc)
                    raise ConnectionError(f"TLE API returned HTTP {exc.response.status_code}.") from exc
                except Exception as exc:
                    logger.error("TLE API unexpected error (attempt %d/%d): %s", attempt + 1, max_retries, exc)
                    if attempt == max_retries - 1:
                        raise ConnectionError(f"TLE API error: {exc}") from exc
                    await asyncio.sleep(2 ** attempt)

    # ------------------------------------------------------------------ #
    # Cache helpers                                                         #
    # ------------------------------------------------------------------ #

    def _cache_get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None or entry.is_expired:
            return None
        return entry.data

    def _cache_set(self, key: str, data: Any, ttl: int) -> None:
        self._cache[key] = CacheEntry(data=data, fetched_at=time.time(), ttl_seconds=ttl)

    # ------------------------------------------------------------------ #
    # Public API                                                            #
    # ------------------------------------------------------------------ #

    async def fetch_by_catnr(self, catnr: int) -> list[dict]:
        """
        Fetch a single satellite by NORAD ID.
        GET /api/tle/{catnr}
        Returns a list with one normalized dict, or empty list if not found.
        """
        cache_key = f"catnr:{catnr}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        url = f"{BASE_URL}{catnr}"
        data = await self._get_json(url)

        if data is None or not isinstance(data, dict):
            result = []
        else:
            result = [_normalize(data)]

        self._cache_set(cache_key, result, SINGLE_TTL)
        return result

    async def fetch_by_name(self, query: str) -> list[dict]:
        """
        Search satellites by name.
        GET /api/tle?search=<query>  (paginates automatically)
        Returns normalized list.
        """
        cache_key = f"name:{query}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        result = await self._paginate_search(query)
        self._cache_set(cache_key, result, SINGLE_TTL)
        return result

    async def fetch_group(self, group: str, limit: int = 500) -> list[dict]:
        """
        Fetch a debris/satellite group by search query.
        Maps old group names to search terms where needed.
        Returns up to `limit` normalized records.
        """
        cache_key = f"group:{group}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        # Map old CelesTrak group names → search terms
        group_map = {
            "cosmos-2251-debris": "COSMOS DEB",
            "iridium-33-debris": "IRIDIUM DEB",
            "cosmos-1408-debris": "COSMOS DEB",
            "active": "COSMOS DEB",   # fallback for generic "active" group
            "debris": "COSMOS DEB",
            "analyst": "IRIDIUM DEB",
        }
        search_term = group_map.get(group.lower(), group.upper())
        result = await self._paginate_search(search_term, max_results=limit)

        self._cache_set(cache_key, result, GROUP_TTL)
        return result

    async def fetch_debris_catalog(self, max_per_query: int = 400) -> list[dict]:
        """
        Fetch all debris objects from the 4 major debris clouds.
        Paginates each search query until exhausted or max_per_query reached.
        Returns a flat deduplicated list of normalized TLE dicts.
        """
        cache_key = f"debris_catalog:{max_per_query}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        seen_ids: set[int] = set()
        all_records: list[dict] = []

        for search_term in DEBRIS_SEARCHES:
            records = await self._paginate_search(search_term, max_results=max_per_query)
            for rec in records:
                norad_id = rec.get("satelliteId")
                if norad_id and norad_id not in seen_ids:
                    seen_ids.add(norad_id)
                    all_records.append(rec)

        self._cache_set(cache_key, all_records, GROUP_TTL)
        return all_records

    async def health_check(self) -> bool:
        """Check API availability by fetching ISS (NORAD 25544)."""
        try:
            result = await self.fetch_by_catnr(25544)
            return len(result) > 0
        except Exception as exc:
            logger.warning("TLE API health check failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    # Pagination helper                                                     #
    # ------------------------------------------------------------------ #

    async def _paginate_search(self, search_term: str, max_results: int = 500) -> list[dict]:
        """
        Paginate GET /api/tle?search=<term> until all results are fetched
        or max_results is reached.
        """
        results: list[dict] = []
        page = 1

        while len(results) < max_results:
            params = {"search": search_term, "page": page, "page-size": 100}
            data = await self._get_json(BASE_URL, params=params)

            if not isinstance(data, dict):
                break

            members = data.get("member", [])
            if not members:
                break

            for item in members:
                if len(results) >= max_results:
                    break
                if isinstance(item, dict):
                    results.append(_normalize(item))

            total = data.get("totalItems", 0)
            if len(results) >= total:
                break

            page += 1

        return results
