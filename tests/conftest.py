"""
Pytest configuration and fixtures for OrbitGuard tests.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies import celestrak_client
from routers import conjunction, groups, satellite, search


@pytest.fixture
def mock_celestrak_client():
    """Mock CelesTrak client for testing."""
    mock_client = AsyncMock()
    mock_client.fetch_by_name = AsyncMock(return_value=[
        {"name": "TURKSAT 4A", "norad_id": 39522},
        {"name": "TURKSAT 4B", "norad_id": 40984},
    ])
    mock_client.fetch_by_catnr = AsyncMock(return_value=[
        {"name": "TURKSAT 4A", "norad_id": 39522}
    ])
    mock_client.fetch_group = AsyncMock(return_value=[
        {"name": "SAT1", "norad_id": 1},
        {"name": "SAT2", "norad_id": 2},
    ])
    mock_client.health_check = AsyncMock(return_value=True)
    return mock_client


@pytest.fixture
def client():
    """Create a test app without IP middleware."""
    from datetime import datetime, timezone
    
    test_app = FastAPI(title="OrbitGuard-Test", version="1.0")
    
    # Include routers without middleware
    test_app.include_router(search.router)
    test_app.include_router(satellite.router)
    test_app.include_router(groups.router)
    test_app.include_router(conjunction.router)
    
    # Add health and root endpoints
    @test_app.get("/")
    async def root():
        return {"status": "ok", "version": "1.0"}
    
    @test_app.get("/health")
    async def health():
        celestrak_ok = await celestrak_client.health_check()
        return {
            "status": "ok",
            "celestrak_ok": celestrak_ok,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    return TestClient(test_app)
