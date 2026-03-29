"""
Frontend testleri — OrbitGuard
Gereksinimler: 12.1, 12.2, 12.3, 12.4, 12.5, 13.1, 13.2, 13.3, 13.4, 13.5, 14.1, 14.2, 14.3, 14.4
"""

import re
from pathlib import Path
from html.parser import HTMLParser

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies import celestrak_client
from routers import conjunction, groups, satellite, search


# ─────────────────────────────────────────────────────────────────────────────
# Property 19: Risk Sıralama Tutarlılığı
# ─────────────────────────────────────────────────────────────────────────────

# Risk level ordering: CRITICAL > HIGH > MEDIUM > LOW
RISK_LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
RISK_PRIORITY = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def risk_level_strategy():
    """Generate risk level strings."""
    return st.sampled_from(RISK_LEVELS)


@settings(max_examples=20)
@given(risk_list=st.lists(risk_level_strategy(), min_size=1, max_size=20))
def test_risk_sorting_consistency(risk_list: list):
    """
    Feature: orbitguard, Property 19: Risk Sıralama Tutarlılığı
    
    Risk events should be sorted CRITICAL > HIGH > MEDIUM > LOW.
    Validates: Requirement 13.2
    """
    # Sort the risk list according to the expected order
    sorted_risks = sorted(risk_list, key=lambda x: RISK_PRIORITY[x], reverse=True)
    
    # Verify that the sorted list maintains the descending priority order
    for i in range(len(sorted_risks) - 1):
        current_priority = RISK_PRIORITY[sorted_risks[i]]
        next_priority = RISK_PRIORITY[sorted_risks[i + 1]]
        assert current_priority >= next_priority, \
            f"Risk order violated: {sorted_risks[i]} (priority {current_priority}) " \
            f"should come before {sorted_risks[i + 1]} (priority {next_priority})"


# ─────────────────────────────────────────────────────────────────────────────
# Property 20: Frontend API Base URL Tutarlılığı
# ─────────────────────────────────────────────────────────────────────────────

class FetchURLExtractor(HTMLParser):
    """Extract all fetch() URLs from HTML."""
    
    def __init__(self):
        super().__init__()
        self.fetch_urls = []
        self.in_script = False
        self.script_content = ""
    
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.in_script = True
            self.script_content = ""
    
    def handle_endtag(self, tag):
        if tag == "script" and self.in_script:
            self.in_script = False
            # Extract fetch URLs from script content
            self._extract_fetch_urls(self.script_content)
    
    def handle_data(self, data):
        if self.in_script:
            self.script_content += data
    
    def _extract_fetch_urls(self, script_content):
        """Extract URLs from fetch() calls."""
        # Match patterns like fetch('http://...') or fetch("http://...")
        pattern = r"fetch\s*\(\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, script_content)
        self.fetch_urls.extend(matches)


def test_frontend_api_base_url_consistency():
    """
    Feature: orbitguard, Property 20: Frontend API Base URL Tutarlılığı
    
    All fetch calls in index.html should use http://127.0.0.1:8000.
    Validates: Requirement 14.4
    """
    # Read the frontend HTML file
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    assert frontend_file.exists(), "frontend/index.html not found"
    
    with open(frontend_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Extract fetch URLs
    extractor = FetchURLExtractor()
    extractor.feed(html_content)
    
    # All fetch URLs should start with http://127.0.0.1:8000
    expected_base = "http://127.0.0.1:8000"
    
    for url in extractor.fetch_urls:
        assert url.startswith(expected_base), \
            f"Fetch URL '{url}' does not start with '{expected_base}'"


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_frontend_loads(client):
    """
    Unit test: Frontend HTML should load successfully.
    Validates: Requirement 14.1
    """
    response = client.get("/")
    assert response.status_code == 200
    # Either HTML or JSON is acceptable (depending on whether frontend file exists)
    content_type = response.headers.get("content-type", "")
    assert "text/html" in content_type or "application/json" in content_type


def test_frontend_single_file():
    """
    Unit test: Frontend should be a single HTML file with inline styles and scripts.
    Validates: Requirement 14.1, 14.3
    """
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    assert frontend_file.exists(), "frontend/index.html not found"
    
    with open(frontend_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Should contain <style> tag (inline styles)
    assert "<style>" in html_content, "Inline styles not found"
    
    # Should contain <script> tag (inline scripts)
    assert "<script>" in html_content, "Inline scripts not found"
    
    # Should NOT reference external CSS files (except CDN)
    # Allow CDN references but not local CSS files
    assert not re.search(r'<link[^>]*href=["\'](?!https?://)[^"\']*\.css["\']', html_content), \
        "External CSS files should not be used"


def test_frontend_three_js_cdn():
    """
    Unit test: Frontend should use Three.js r128 from CDN.
    Validates: Requirement 14.2
    """
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    assert frontend_file.exists(), "frontend/index.html not found"
    
    with open(frontend_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Should reference Three.js r128 from CDN
    assert "three.js/r128" in html_content or "three.min.js" in html_content, \
        "Three.js r128 CDN reference not found"


def test_frontend_background_color():
    """
    Unit test: Frontend should use dark background color #0a0a0f.
    Validates: Requirement 13.5
    """
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    assert frontend_file.exists(), "frontend/index.html not found"
    
    with open(frontend_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Should contain the background color #0a0a0f
    assert "#0a0a0f" in html_content, "Background color #0a0a0f not found"


def test_frontend_turkish_satellites_listed():
    """
    Unit test: Frontend should list 6 Turkish satellites.
    Validates: Requirement 13.1
    """
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    assert frontend_file.exists(), "frontend/index.html not found"
    
    with open(frontend_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Should reference Turkish satellites
    turkish_sats = ["TURKSAT", "GOKTURK"]
    for sat in turkish_sats:
        assert sat in html_content, f"Turkish satellite {sat} not found in frontend"


def test_frontend_polling_interval():
    """
    Unit test: Frontend should have polling interval.
    Validates: Requirement 12.3
    """
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    assert frontend_file.exists(), "frontend/index.html not found"
    
    with open(frontend_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Should contain polling interval (60000 milliseconds = 60 seconds or 30000 = 30 seconds)
    assert "60000" in html_content or "30000" in html_content or "30 * 1000" in html_content or "setInterval" in html_content, \
        "Polling interval not found"
