"""
Property-based and unit tests for LocalOnlyMiddleware.
Tests that non-local IPs receive HTTP 403 and local IPs pass through.

**Validates: Requirements 1.2, 1.3, 1.4, 1.5**
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hypothesis import given, settings, strategies as st, HealthCheck
from starlette.requests import Request
from starlette.responses import JSONResponse

from middleware import LocalOnlyMiddleware


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _make_app() -> FastAPI:
    """Create a minimal FastAPI app with LocalOnlyMiddleware."""
    app = FastAPI()
    app.add_middleware(LocalOnlyMiddleware)

    @app.get("/ping")
    async def ping():
        return {"pong": True}

    return app


def _client_with_ip(ip: str) -> TestClient:
    """Return a TestClient that spoofs the given client IP."""
    app = _make_app()
    return TestClient(app, base_url=f"http://{ip}")


class TestLocalOnlyMiddleware:
    def test_localhost_ipv4_allowed(self, event_loop):
        """127.0.0.1 should pass through (not 403)."""
        app = _make_app()
        mw = LocalOnlyMiddleware(app)

        async def run():
            request = MagicMock(spec=Request)
            request.client = MagicMock()
            request.client.host = "127.0.0.1"
            call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
            response = await mw.dispatch(request, call_next)
            return response

        resp = event_loop.run_until_complete(run())
        assert resp.status_code == 200

    def test_loopback_ipv6_allowed(self, event_loop):
        """::1 should pass through."""
        app = _make_app()
        mw = LocalOnlyMiddleware(app)

        async def run():
            request = MagicMock(spec=Request)
            request.client = MagicMock()
            request.client.host = "::1"
            call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
            response = await mw.dispatch(request, call_next)
            return response

        resp = event_loop.run_until_complete(run())
        assert resp.status_code == 200

    def test_external_ip_forbidden(self, event_loop):
        """Non-local IP should receive HTTP 403."""
        app = _make_app()
        mw = LocalOnlyMiddleware(app)

        async def run():
            request = MagicMock(spec=Request)
            request.client = MagicMock()
            request.client.host = "203.0.113.42"
            call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
            response = await mw.dispatch(request, call_next)
            return response

        resp = event_loop.run_until_complete(run())
        assert resp.status_code == 403

    def test_private_ip_forbidden(self, event_loop):
        """Private network IP (192.168.x.x) should also receive 403."""
        app = _make_app()
        mw = LocalOnlyMiddleware(app)

        async def run():
            request = MagicMock(spec=Request)
            request.client = MagicMock()
            request.client.host = "192.168.1.100"
            call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
            response = await mw.dispatch(request, call_next)
            return response

        resp = event_loop.run_until_complete(run())
        assert resp.status_code == 403

    def test_no_client_forbidden(self, event_loop):
        """Request with no client info should receive 403."""
        app = _make_app()
        mw = LocalOnlyMiddleware(app)

        async def run():
            request = MagicMock(spec=Request)
            request.client = None
            call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
            response = await mw.dispatch(request, call_next)
            return response

        resp = event_loop.run_until_complete(run())
        assert resp.status_code == 403


# Property-based test using Hypothesis
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(ip=st.ip_addresses())
def test_ip_filter_property(ip, event_loop):
    """
    Feature: orbitguard, Property 1: IP Filtresi — Her İki Servis
    
    For any HTTP request:
    - If source IP is 127.0.0.1 or ::1, request should pass through (not 403)
    - If source IP is anything else, both Backend and Camera Service should return HTTP 403
    
    **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    """
    app = _make_app()
    mw = LocalOnlyMiddleware(app)

    async def run():
        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = str(ip)
        call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
        response = await mw.dispatch(request, call_next)
        return response

    resp = event_loop.run_until_complete(run())

    # Check the property: local IPs pass, others get 403
    if str(ip) in {"127.0.0.1", "::1"}:
        assert resp.status_code == 200, f"Local IP {ip} should pass through"
    else:
        assert resp.status_code == 403, f"Non-local IP {ip} should receive 403"
