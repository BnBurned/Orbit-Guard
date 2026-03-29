"""
Property-based and unit tests for CelesTrakClient User-Agent header.
Tests that every CelesTrak API request includes the User-Agent: OrbitGuard/1.0 header.

**Validates: Requirement 2.1**
"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st

from celestrak_client import CelesTrakClient, USER_AGENT


class TestUserAgentHeader:
    """Unit tests for User-Agent header requirement."""

    def test_fetch_group_includes_user_agent(self):
        """fetch_group should include User-Agent header in request."""
        client = CelesTrakClient()
        
        # Mock the httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "OBJECT_NAME": "TURKSAT 4A",
                "NORAD_CAT_ID": 39522,
                "TLE_LINE1": "1 39522U 13055A   24001.00000000  .00000000  00000-0  00000-0 0    00",
                "TLE_LINE2": "2 39522   0.0000 000.0000 0000000  00.0000 000.0000  1.00273791    00",
            }
        ]
        mock_response.raise_for_status = MagicMock()
        
        with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            asyncio.run(client.fetch_group("active"))
            
            # Verify that AsyncClient was called with the correct headers
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["User-Agent"] == USER_AGENT
            assert call_kwargs["headers"]["User-Agent"] == "OrbitGuard/1.0"

    def test_fetch_by_catnr_includes_user_agent(self):
        """fetch_by_catnr should include User-Agent header in request."""
        client = CelesTrakClient()
        
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "OBJECT_NAME": "TURKSAT 4A",
                "NORAD_CAT_ID": 39522,
                "TLE_LINE1": "1 39522U 13055A   24001.00000000  .00000000  00000-0  00000-0 0    00",
                "TLE_LINE2": "2 39522   0.0000 000.0000 0000000  00.0000 000.0000  1.00273791    00",
            }
        ]
        mock_response.raise_for_status = MagicMock()
        
        with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            asyncio.run(client.fetch_by_catnr(39522))
            
            # Verify that AsyncClient was called with the correct headers
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["User-Agent"] == "OrbitGuard/1.0"

    def test_fetch_by_name_includes_user_agent(self):
        """fetch_by_name should include User-Agent header in request."""
        client = CelesTrakClient()
        
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "OBJECT_NAME": "TURKSAT 4A",
                "NORAD_CAT_ID": 39522,
                "TLE_LINE1": "1 39522U 13055A   24001.00000000  .00000000  00000-0  00000-0 0    00",
                "TLE_LINE2": "2 39522   0.0000 000.0000 0000000  00.0000 000.0000  1.00273791    00",
            }
        ]
        mock_response.raise_for_status = MagicMock()
        
        with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            asyncio.run(client.fetch_by_name("TURKSAT"))
            
            # Verify that AsyncClient was called with the correct headers
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["User-Agent"] == "OrbitGuard/1.0"

    def test_health_check_includes_user_agent(self):
        """health_check should include User-Agent header in request."""
        client = CelesTrakClient()
        
        mock_response = MagicMock()
        mock_response.json.return_value = [{"NORAD_CAT_ID": 25544}]
        mock_response.raise_for_status = MagicMock()
        
        with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            asyncio.run(client.health_check())
            
            # Verify that AsyncClient was called with the correct headers
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["User-Agent"] == "OrbitGuard/1.0"


# Property-based test using Hypothesis
@settings(max_examples=100)
@given(
    group=st.text(min_size=1, max_size=50),
    limit=st.integers(min_value=1, max_value=500),
)
def test_fetch_group_user_agent_property(group, limit):
    """
    Feature: orbitguard, Property 2: User-Agent Başlığı Zorunluluğu
    
    For any CelesTrak GP API call via fetch_group:
    - The HTTP request must include User-Agent header with exact value "OrbitGuard/1.0"
    
    **Validates: Requirement 2.1**
    """
    client = CelesTrakClient()
    
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "OBJECT_NAME": "TEST_SAT",
            "NORAD_CAT_ID": 12345,
            "TLE_LINE1": "1 12345U 20001A   24001.00000000  .00000000  00000-0  00000-0 0    00",
            "TLE_LINE2": "2 12345   0.0000 000.0000 0000000  00.0000 000.0000  1.00273791    00",
        }
    ]
    mock_response.raise_for_status = MagicMock()
    
    with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Run the async function
        asyncio.run(client.fetch_group(group, limit))
        
        # Verify that AsyncClient was called with the correct headers
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert "headers" in call_kwargs, "Headers must be provided to AsyncClient"
        assert call_kwargs["headers"]["User-Agent"] == "OrbitGuard/1.0", \
            f"User-Agent must be exactly 'OrbitGuard/1.0', got {call_kwargs['headers'].get('User-Agent')}"


@settings(max_examples=100)
@given(catnr=st.integers(min_value=1, max_value=99999))
def test_fetch_by_catnr_user_agent_property(catnr):
    """
    Feature: orbitguard, Property 2: User-Agent Başlığı Zorunluluğu
    
    For any CelesTrak GP API call via fetch_by_catnr:
    - The HTTP request must include User-Agent header with exact value "OrbitGuard/1.0"
    
    **Validates: Requirement 2.1**
    """
    client = CelesTrakClient()
    
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "OBJECT_NAME": "TEST_SAT",
            "NORAD_CAT_ID": catnr,
            "TLE_LINE1": "1 12345U 20001A   24001.00000000  .00000000  00000-0  00000-0 0    00",
            "TLE_LINE2": "2 12345   0.0000 000.0000 0000000  00.0000 000.0000  1.00273791    00",
        }
    ]
    mock_response.raise_for_status = MagicMock()
    
    with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Run the async function
        asyncio.run(client.fetch_by_catnr(catnr))
        
        # Verify that AsyncClient was called with the correct headers
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert "headers" in call_kwargs, "Headers must be provided to AsyncClient"
        assert call_kwargs["headers"]["User-Agent"] == "OrbitGuard/1.0", \
            f"User-Agent must be exactly 'OrbitGuard/1.0', got {call_kwargs['headers'].get('User-Agent')}"


@settings(max_examples=100)
@given(query=st.text(min_size=1, max_size=100))
def test_fetch_by_name_user_agent_property(query):
    """
    Feature: orbitguard, Property 2: User-Agent Başlığı Zorunluluğu
    
    For any CelesTrak GP API call via fetch_by_name:
    - The HTTP request must include User-Agent header with exact value "OrbitGuard/1.0"
    
    **Validates: Requirement 2.1**
    """
    client = CelesTrakClient()
    
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "OBJECT_NAME": "TEST_SAT",
            "NORAD_CAT_ID": 12345,
            "TLE_LINE1": "1 12345U 20001A   24001.00000000  .00000000  00000-0  00000-0 0    00",
            "TLE_LINE2": "2 12345   0.0000 000.0000 0000000  00.0000 000.0000  1.00273791    00",
        }
    ]
    mock_response.raise_for_status = MagicMock()
    
    with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Run the async function
        asyncio.run(client.fetch_by_name(query))
        
        # Verify that AsyncClient was called with the correct headers
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert "headers" in call_kwargs, "Headers must be provided to AsyncClient"
        assert call_kwargs["headers"]["User-Agent"] == "OrbitGuard/1.0", \
            f"User-Agent must be exactly 'OrbitGuard/1.0', got {call_kwargs['headers'].get('User-Agent')}"


@settings(max_examples=100)
@given(dummy=st.just(None))
def test_health_check_user_agent_property(dummy):
    """
    Feature: orbitguard, Property 2: User-Agent Başlığı Zorunluluğu
    
    For any CelesTrak GP API call via health_check:
    - The HTTP request must include User-Agent header with exact value "OrbitGuard/1.0"
    
    **Validates: Requirement 2.1**
    """
    client = CelesTrakClient()
    
    mock_response = MagicMock()
    mock_response.json.return_value = [{"NORAD_CAT_ID": 25544}]
    mock_response.raise_for_status = MagicMock()
    
    with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Run the async function
        asyncio.run(client.health_check())
        
        # Verify that AsyncClient was called with the correct headers
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert "headers" in call_kwargs, "Headers must be provided to AsyncClient"
        assert call_kwargs["headers"]["User-Agent"] == "OrbitGuard/1.0", \
            f"User-Agent must be exactly 'OrbitGuard/1.0', got {call_kwargs['headers'].get('User-Agent')}"


@settings(max_examples=100)
@given(num_requests=st.integers(min_value=11, max_value=50))
def test_concurrent_request_limit_property(num_requests):
    """
    Feature: orbitguard, Property 3: Eş Zamanlı İstek Sınırı
    
    For any N > 10 concurrent requests to CelesTrak:
    - The maximum number of concurrent active requests must never exceed 10
    - The semaphore ensures that no more than 10 requests are active simultaneously
    
    **Validates: Requirement 2.2**
    """
    # Track concurrent request count
    active_requests = 0
    max_concurrent = 0
    lock = asyncio.Lock()
    
    async def mock_http_get_with_tracking(url, params=None, **kwargs):
        """Mock httpx.AsyncClient.get that tracks concurrent requests."""
        nonlocal active_requests, max_concurrent
        
        async with lock:
            active_requests += 1
            max_concurrent = max(max_concurrent, active_requests)
        
        # Simulate some work
        await asyncio.sleep(0.01)
        
        async with lock:
            active_requests -= 1
        
        # Return mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "OBJECT_NAME": "TEST_SAT",
                "NORAD_CAT_ID": 12345,
                "TLE_LINE1": "1 12345U 20001A   24001.00000000  .00000000  00000-0  00000-0 0    00",
                "TLE_LINE2": "2 12345   0.0000 000.0000 0000000  00.0000 000.0000  1.00273791    00",
            }
        ]
        mock_response.raise_for_status = MagicMock()
        return mock_response
    
    async def run_concurrent_requests():
        """Run N concurrent requests."""
        client = CelesTrakClient()
        
        # Create N concurrent tasks
        tasks = [
            client.fetch_group(f"group_{i}", limit=100)
            for i in range(num_requests)
        ]
        
        # Patch httpx.AsyncClient to use our tracking version
        with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=mock_http_get_with_tracking)
            mock_client_class.return_value = mock_client
            
            await asyncio.gather(*tasks, return_exceptions=True)
    
    # Run the concurrent requests
    asyncio.run(run_concurrent_requests())
    
    # Verify that max concurrent requests never exceeded 10
    assert max_concurrent <= 10, \
        f"Maximum concurrent requests ({max_concurrent}) exceeded limit of 10 when sending {num_requests} requests"


@settings(max_examples=100)
@given(
    elapsed_seconds=st.floats(min_value=0, max_value=1800),
    is_group_query=st.booleans(),
)
def test_cache_ttl_accuracy_property(elapsed_seconds, is_group_query):
    """
    Feature: orbitguard, Property 4: Önbellek TTL Doğruluğu
    
    For any group or individual satellite query:
    - Before TTL expires: second request should hit cache (no CelesTrak call)
    - After TTL expires: request should fetch fresh data from CelesTrak
    
    Group TTL: 900s (15 min)
    Individual TTL: 300s (5 min)
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    client = CelesTrakClient()
    
    # Determine TTL based on query type
    ttl = 900 if is_group_query else 300
    
    # Mock response data
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "OBJECT_NAME": "TEST_SAT",
            "NORAD_CAT_ID": 12345,
            "TLE_LINE1": "1 12345U 20001A   24001.00000000  .00000000  00000-0  00000-0 0    00",
            "TLE_LINE2": "2 12345   0.0000 000.0000 0000000  00.0000 000.0000  1.00273791    00",
        }
    ]
    mock_response.raise_for_status = MagicMock()
    
    async def run_cache_test():
        """Test cache hit/miss behavior with time manipulation."""
        with patch("celestrak_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # First request: should fetch from CelesTrak
            if is_group_query:
                result1 = await client.fetch_group("active", limit=100)
            else:
                result1 = await client.fetch_by_catnr(12345)
            
            # Verify first request was made
            assert mock_client.get.call_count == 1, "First request should call CelesTrak"
            
            # Get the time when the cache entry was created
            original_time = time.time()
            
            # Simulate time passage by patching time.time globally
            with patch("celestrak_client.time.time") as mock_time:
                # Set mock to return time advanced by elapsed_seconds
                mock_time.return_value = original_time + elapsed_seconds
                
                # Second request
                if is_group_query:
                    result2 = await client.fetch_group("active", limit=100)
                else:
                    result2 = await client.fetch_by_catnr(12345)
                
                # Verify cache behavior
                if elapsed_seconds < ttl:
                    # Before TTL expires: should be cache hit (no new CelesTrak call)
                    assert mock_client.get.call_count == 1, \
                        f"Cache hit expected when elapsed ({elapsed_seconds}s) < TTL ({ttl}s), but CelesTrak was called again"
                    assert result1 == result2, "Cached result should match original result"
                else:
                    # After TTL expires: should be cache miss (new CelesTrak call)
                    assert mock_client.get.call_count == 2, \
                        f"Cache miss expected when elapsed ({elapsed_seconds}s) >= TTL ({ttl}s), but CelesTrak was not called"
    
    # Run the async test
    asyncio.run(run_cache_test())
