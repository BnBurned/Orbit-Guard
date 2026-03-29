"""
Tekil uydu router'ı testleri — OrbitGuard
Gereksinimler: 6.1, 6.2, 6.3, 6.4
"""

import pytest
from unittest.mock import AsyncMock, patch
from hypothesis import given, settings, strategies as st, HealthCheck
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies import celestrak_client
from routers import conjunction, groups, satellite, search


# Sample satellite data for mocking
SAMPLE_SATELLITE = {
    "OBJECT_NAME": "TURKSAT 4A",
    "NORAD_CAT_ID": 39522,
    "EPOCH": "2024-01-15T12:34:56.789012",
    "INCLINATION": 0.0,
    "ECCENTRICITY": 0.0001,
    "MEAN_MOTION": 1.0,
    "TLE_LINE1": "1 39522U 13066A   24015.52500000  .00000000  00000-0  00000-0 0  9990",
    "TLE_LINE2": "2 39522   0.0000 000.0000 0000001  00.0000 000.0000  1.00273791000000",
}


# ─────────────────────────────────────────────────────────────────────────────
# Property 9: Uydu Endpoint Şema Bütünlüğü
# ─────────────────────────────────────────────────────────────────────────────

@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(catnr=st.integers(min_value=1, max_value=99999))
def test_satellite_schema_completeness(client, catnr: int):
    """
    Feature: orbitguard, Property 9: Uydu Endpoint Şema Bütünlüğü
    
    All required fields should be present in satellite endpoint responses.
    Validates: Requirements 6.1, 6.2, 6.3
    """
    # Mock the celestrak_client to return sample data
    with patch.object(celestrak_client, 'fetch_by_catnr', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [SAMPLE_SATELLITE]
        
        # Test main satellite endpoint
        response = client.get(f"/api/satellite/{catnr}")
        
        # Should be 200
        assert response.status_code == 200
        data = response.json()
        
        # Check for all required fields in main endpoint
        required_fields = [
            "name", "norad_id", "epoch", "inclination", "eccentricity",
            "altitude_km", "period_min", "orbit_type", "tle_line1", "tle_line2"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify field types
        assert isinstance(data["name"], str)
        assert isinstance(data["norad_id"], int)
        assert isinstance(data["epoch"], str)
        assert isinstance(data["inclination"], (int, float))
        assert isinstance(data["eccentricity"], (int, float))
        assert isinstance(data["altitude_km"], (int, float))
        assert isinstance(data["period_min"], (int, float))
        assert isinstance(data["orbit_type"], str)
        assert isinstance(data["tle_line1"], str)
        assert isinstance(data["tle_line2"], str)


@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(catnr=st.integers(min_value=1, max_value=99999))
def test_satellite_position_schema(client, catnr: int):
    """
    Unit test: Position endpoint should have correct schema.
    Validates: Requirement 6.2
    """
    # Mock the celestrak_client to return sample data
    with patch.object(celestrak_client, 'fetch_by_catnr', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [SAMPLE_SATELLITE]
        
        response = client.get(f"/api/satellite/{catnr}/position")
        
        # Should be 200
        assert response.status_code == 200
        data = response.json()
        
        # Check for required fields
        assert "eci" in data
        assert "geodetic" in data
        assert "velocity" in data
        
        # Check ECI structure
        assert "x" in data["eci"]
        assert "y" in data["eci"]
        assert "z" in data["eci"]
        
        # Check geodetic structure
        assert "lat" in data["geodetic"]
        assert "lon" in data["geodetic"]
        assert "alt_km" in data["geodetic"]
        
        # Check velocity structure
        assert "vx" in data["velocity"]
        assert "vy" in data["velocity"]
        assert "vz" in data["velocity"]
        
        # Verify coordinate validity
        assert -90 <= data["geodetic"]["lat"] <= 90, "Latitude out of range"
        assert -180 <= data["geodetic"]["lon"] <= 180, "Longitude out of range"
        assert data["geodetic"]["alt_km"] >= 0, "Altitude should be non-negative"


@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(catnr=st.integers(min_value=1, max_value=99999))
def test_satellite_orbital_schema(client, catnr: int):
    """
    Unit test: Orbital endpoint should have correct schema.
    Validates: Requirement 6.3
    """
    # Mock the celestrak_client to return sample data
    with patch.object(celestrak_client, 'fetch_by_catnr', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [SAMPLE_SATELLITE]
        
        response = client.get(f"/api/satellite/{catnr}/orbital")
        
        # Should be 200
        assert response.status_code == 200
        data = response.json()
        
        # Check for required fields
        required_fields = [
            "perigee_km", "apogee_km", "period_min", "inclination_deg", "orbit_type"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify field types
        assert isinstance(data["perigee_km"], (int, float))
        assert isinstance(data["apogee_km"], (int, float))
        assert isinstance(data["period_min"], (int, float))
        assert isinstance(data["inclination_deg"], (int, float))
        assert isinstance(data["orbit_type"], str)


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_satellite_not_found_returns_404(client):
    """
    Unit test: Non-existent satellite should return 404.
    Validates: Requirement 6.4
    """
    # Mock the celestrak_client to return empty list
    with patch.object(celestrak_client, 'fetch_by_catnr', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        
        response = client.get("/api/satellite/999999999")
        assert response.status_code == 404


def test_satellite_position_not_found_returns_404(client):
    """
    Unit test: Position endpoint for non-existent satellite should return 404.
    Validates: Requirement 6.4
    """
    # Mock the celestrak_client to return empty list
    with patch.object(celestrak_client, 'fetch_by_catnr', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        
        response = client.get("/api/satellite/999999999/position")
        assert response.status_code == 404


def test_satellite_orbital_not_found_returns_404(client):
    """
    Unit test: Orbital endpoint for non-existent satellite should return 404.
    Validates: Requirement 6.4
    """
    # Mock the celestrak_client to return empty list
    with patch.object(celestrak_client, 'fetch_by_catnr', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        
        response = client.get("/api/satellite/999999999/orbital")
        assert response.status_code == 404
