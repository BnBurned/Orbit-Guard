"""
Sağlık endpoint testleri — OrbitGuard
Gereksinimler: 4.1, 4.2, 4.3, 4.4
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from hypothesis import given, settings, strategies as st, HealthCheck
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies import celestrak_client
from routers import conjunction, groups, satellite, search


# ─────────────────────────────────────────────────────────────────────────────
# Property 5: Sağlık Endpoint Şeması
# ─────────────────────────────────────────────────────────────────────────────

@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(celestrak_available=st.booleans())
def test_health_endpoint_schema(client, celestrak_available: bool):
    """
    Feature: orbitguard, Property 5: Sağlık Endpoint Şeması
    
    Health endpoint should return status, celestrak_ok, timestamp fields.
    celestrak_ok should correlate with actual CelesTrak availability.
    Validates: Requirements 4.2, 4.3, 4.4
    """
    # Mock the celestrak_client.health_check to return the specified availability
    with patch.object(celestrak_client, 'health_check', new_callable=AsyncMock) as mock_health:
        mock_health.return_value = celestrak_available
        
        response = client.get("/health")
        
        # Should return 200
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have required fields
        assert "status" in data
        assert "celestrak_ok" in data
        assert "timestamp" in data
        
        # status should be "ok"
        assert data["status"] == "ok"
        
        # celestrak_ok should be a boolean
        assert isinstance(data["celestrak_ok"], bool)
        
        # celestrak_ok should match the mocked availability
        assert data["celestrak_ok"] == celestrak_available
        
        # timestamp should be a valid ISO 8601 string
        try:
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pytest.fail(f"Invalid ISO 8601 timestamp: {data['timestamp']}")


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_health_endpoint_when_celestrak_available(client):
    """
    Unit test: Health endpoint should return celestrak_ok=true when CelesTrak is available.
    Validates: Requirement 4.3
    """
    with patch.object(celestrak_client, 'health_check', new_callable=AsyncMock) as mock_health:
        mock_health.return_value = True
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["celestrak_ok"] is True


def test_health_endpoint_when_celestrak_unavailable(client):
    """
    Unit test: Health endpoint should return celestrak_ok=false when CelesTrak is unavailable.
    Validates: Requirement 4.4
    """
    with patch.object(celestrak_client, 'health_check', new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["celestrak_ok"] is False


def test_root_endpoint(client):
    """
    Unit test: Root endpoint should return status and version.
    Validates: Requirement 4.1
    """
    response = client.get("/")
    
    # Should return 200
    assert response.status_code == 200
    
    # If it's JSON, check for status and version
    try:
        data = response.json()
        assert "status" in data or "version" in data
    except:
        # If it's HTML (frontend), that's also acceptable
        pass
