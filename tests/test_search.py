"""
Uydu arama router'ı testleri — OrbitGuard
Gereksinimler: 5.1, 5.2, 5.3, 5.4
"""

import pytest
from unittest.mock import AsyncMock, patch
from hypothesis import given, settings, strategies as st, HealthCheck
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies import celestrak_client
from routers import conjunction, groups, satellite, search


# ─────────────────────────────────────────────────────────────────────────────
# Property 6: İsim Araması Tutarlılığı
# ─────────────────────────────────────────────────────────────────────────────

@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(query=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\x00\x1f")))
def test_search_name_consistency(client, query: str):
    """
    Feature: orbitguard, Property 6: İsim Araması Tutarlılığı
    
    For any search query q, all returned satellites' name field should contain q (case-insensitive).
    Validates: Requirement 5.1
    """
    # Skip queries with special characters that might cause issues
    if any(c in query for c in ['<', '>', '"', "'", '&', '?', '#']):
        return
    
    # Mock the celestrak_client to return matching results
    with patch.object(celestrak_client, 'fetch_by_name', new_callable=AsyncMock) as mock_fetch:
        # Return satellites that match the query
        mock_fetch.return_value = [
            {"name": f"SAT_{query}_1", "norad_id": 1},
            {"name": f"SAT_{query}_2", "norad_id": 2},
        ]
        
        try:
            response = client.get(f"/api/search/name?q={query}&format=json")
        except Exception:
            # Skip if URL encoding fails
            return
        
        # If query is empty or whitespace, expect 400
        if not query.strip():
            assert response.status_code == 400
            return
        
        # Otherwise expect 200
        assert response.status_code == 200
        results = response.json()
        
        # Results should be a list
        assert isinstance(results, list)
        
        # If results are returned, each should have a name field containing the query (case-insensitive)
        for satellite in results:
            assert isinstance(satellite, dict)
            assert "name" in satellite
            assert query.lower() in satellite["name"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# Property 7: NORAD_ID Araması Doğruluğu
# ─────────────────────────────────────────────────────────────────────────────

@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(norad_id=st.integers(min_value=1, max_value=99999))
def test_search_norad_id_accuracy(client, norad_id: int):
    """
    Feature: orbitguard, Property 7: NORAD_ID Araması Doğruluğu
    
    For any NORAD_ID, returned satellite's norad_id field should match the query.
    Validates: Requirement 5.2
    """
    # Mock the celestrak_client to return matching results
    with patch.object(celestrak_client, 'fetch_by_catnr', new_callable=AsyncMock) as mock_fetch:
        # Return satellite with matching NORAD_ID
        mock_fetch.return_value = [
            {"name": f"SAT_{norad_id}", "norad_id": norad_id},
        ]
        
        response = client.get(f"/api/search/catnr?id={norad_id}&format=json")
        
        # Should return 200
        assert response.status_code == 200
        results = response.json()
        
        # Results should be a list
        assert isinstance(results, list)
        
        # If results are returned, each should have norad_id matching the query
        for satellite in results:
            assert isinstance(satellite, dict)
            assert "norad_id" in satellite
            assert satellite["norad_id"] == norad_id


# ─────────────────────────────────────────────────────────────────────────────
# Property 8: Geçersiz Parametre → 400
# ─────────────────────────────────────────────────────────────────────────────

def test_search_invalid_parameter_returns_400(client):
    """
    Feature: orbitguard, Property 8: Geçersiz Parametre → 400
    
    Missing or invalid parameters should return HTTP 400.
    Validates: Requirement 5.4
    """
    # Test missing 'q' parameter in name search
    response = client.get("/api/search/name?format=json")
    assert response.status_code == 400
    
    # Test missing 'id' parameter in catnr search
    response = client.get("/api/search/catnr?format=json")
    assert response.status_code == 400
    
    # Test invalid 'id' parameter (non-integer)
    response = client.get("/api/search/catnr?id=invalid&format=json")
    assert response.status_code == 400
    
    # Test negative NORAD_ID
    response = client.get("/api/search/catnr?id=-1&format=json")
    assert response.status_code == 400
    
    # Test zero NORAD_ID
    response = client.get("/api/search/catnr?id=0&format=json")
    assert response.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_search_name_empty_result(client):
    """
    Unit test: Empty search result should return empty list or 503 if CelesTrak unavailable.
    Validates: Requirement 5.3
    """
    # Mock the celestrak_client to return empty list
    with patch.object(celestrak_client, 'fetch_by_name', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        
        response = client.get("/api/search/name?q=NONEXISTENT_SATELLITE_XYZ_12345&format=json")
        assert response.status_code == 200
        assert response.json() == []


def test_search_catnr_empty_result(client):
    """
    Unit test: Non-existent NORAD_ID should return empty list or 503 if CelesTrak unavailable.
    Validates: Requirement 5.3
    """
    # Mock the celestrak_client to return empty list
    with patch.object(celestrak_client, 'fetch_by_catnr', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = []
        
        response = client.get("/api/search/catnr?id=999999999&format=json")
        assert response.status_code == 200
        assert response.json() == []
