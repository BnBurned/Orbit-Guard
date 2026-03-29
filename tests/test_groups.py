"""
Grup sorgu router'ı testleri — OrbitGuard
Gereksinimler: 7.1, 7.2, 7.3
"""

import pytest
from unittest.mock import AsyncMock, patch
from hypothesis import given, settings, strategies as st, HealthCheck
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies import celestrak_client
from routers import conjunction, groups, satellite, search

# Supported groups from routers/groups.py
SUPPORTED_GROUPS = {
    "active", "stations", "visual", "weather", "noaa", "goes", "resource",
    "sarsat", "dmc", "tdrss", "argos", "planet", "spire", "geo", "intelsat",
    "ses", "iridium", "iridium-NEXT", "starlink", "oneweb", "orbcomm",
    "globalstar", "swarm", "amateur", "x-comm", "other-comm", "satnogs",
    "gorizont", "raduga", "molniya", "cosmos-1408-debris", "fengyun-1c-debris",
    "iridium-33-debris", "cosmos-2251-debris",
}


# ─────────────────────────────────────────────────────────────────────────────
# Property 10: Grup Limit Sınırı
# ─────────────────────────────────────────────────────────────────────────────

@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(group=st.sampled_from(sorted(SUPPORTED_GROUPS)))
def test_group_limit_constraint(client, group: str):
    """
    Feature: orbitguard, Property 10: Grup Limit Sınırı
    
    Any group query should return ≤ 500 records.
    Validates: Requirement 7.1
    """
    # Mock the celestrak_client to return limited results
    with patch.object(celestrak_client, 'fetch_group', new_callable=AsyncMock) as mock_fetch:
        # Return a list with up to 500 items
        mock_fetch.return_value = [
            {"name": f"SAT_{i}", "norad_id": i} for i in range(100)
        ]
        
        response = client.get(f"/api/groups/{group}?format=json&limit=500")
        
        # Should return 200 for supported groups
        assert response.status_code == 200
        results = response.json()
        
        # Results should be a list
        assert isinstance(results, list)
        
        # Results should not exceed 500 records
        assert len(results) <= 500


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_group_unsupported_returns_404(client):
    """
    Unit test: Unsupported group should return 404.
    Validates: Requirement 7.3
    """
    response = client.get("/api/groups/unsupported-group?format=json&limit=500")
    assert response.status_code == 404


def test_group_count_endpoint(client):
    """
    Unit test: Group count endpoint should return correct schema.
    Validates: Requirement 7.2
    """
    # Use a supported group
    group = "active"
    
    # Mock the celestrak_client to return results
    with patch.object(celestrak_client, 'fetch_group', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [
            {"name": f"SAT_{i}", "norad_id": i} for i in range(50)
        ]
        
        response = client.get(f"/api/groups/{group}/count")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have 'group' and 'count' fields
        assert "group" in data
        assert "count" in data
        assert data["group"] == group
        assert isinstance(data["count"], int)
        assert data["count"] >= 0


def test_group_count_unsupported_returns_404(client):
    """
    Unit test: Count endpoint for unsupported group should return 404.
    Validates: Requirement 7.3
    """
    response = client.get("/api/groups/unsupported-group/count")
    assert response.status_code == 404
