"""
Smoke tests for ConjunctionEngine._compute_miss_distance.
Tests that miss distance is always non-negative.
"""
import math
import pytest
from hypothesis import given, settings, strategies as st
from datetime import datetime, timezone

from conjunction import ConjunctionEngine, _risk_level


class TestComputeMissDistance:
    def test_same_position_is_zero(self):
        """Two objects at the same position should have zero miss distance."""
        pos = (1000.0, 2000.0, 3000.0)
        dist = ConjunctionEngine._compute_miss_distance(pos, pos)
        assert dist == pytest.approx(0.0)

    def test_known_distance(self):
        """Simple 3-4-5 right triangle should give distance 5."""
        pos1 = (0.0, 0.0, 0.0)
        pos2 = (3.0, 4.0, 0.0)
        dist = ConjunctionEngine._compute_miss_distance(pos1, pos2)
        assert dist == pytest.approx(5.0)

    def test_non_negative_for_arbitrary_positions(self):
        """Miss distance must always be >= 0 for any two positions."""
        test_cases = [
            ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
            ((100.0, 200.0, 300.0), (-100.0, -200.0, -300.0)),
            ((6371.0, 0.0, 0.0), (0.0, 6371.0, 0.0)),
            ((42164.0, 0.0, 0.0), (42164.0, 1.0, 0.0)),
        ]
        for pos1, pos2 in test_cases:
            dist = ConjunctionEngine._compute_miss_distance(pos1, pos2)
            assert dist >= 0.0, f"Expected non-negative distance for {pos1}, {pos2}"

    def test_symmetry(self):
        """Distance from A to B should equal distance from B to A."""
        pos1 = (1000.0, 2000.0, 3000.0)
        pos2 = (4000.0, 5000.0, 6000.0)
        assert ConjunctionEngine._compute_miss_distance(pos1, pos2) == pytest.approx(
            ConjunctionEngine._compute_miss_distance(pos2, pos1)
        )

    def test_large_geo_orbit_distance(self):
        """Two GEO satellites separated by 1 km should return ~1 km."""
        pos1 = (42164.0, 0.0, 0.0)
        pos2 = (42165.0, 0.0, 0.0)
        dist = ConjunctionEngine._compute_miss_distance(pos1, pos2)
        assert dist == pytest.approx(1.0)


class TestRiskLevel:
    def test_critical_below_1km(self):
        assert _risk_level(0.5) == "CRITICAL"

    def test_high_between_1_and_5km(self):
        assert _risk_level(3.0) == "HIGH"

    def test_medium_between_5_and_10km(self):
        assert _risk_level(7.5) == "MEDIUM"

    def test_low_above_10km(self):
        assert _risk_level(15.0) == "LOW"

    def test_boundary_exactly_1km_is_high(self):
        assert _risk_level(1.0) == "HIGH"

    def test_boundary_exactly_5km_is_medium(self):
        assert _risk_level(5.0) == "MEDIUM"

    def test_boundary_exactly_10km_is_low(self):
        assert _risk_level(10.0) == "LOW"



class TestInclinationFilter:
    """Property-based tests for inclination filter accuracy (P13)."""

    # Real TLE base lines (ISS)
    _BASE_TLE1 = "1 25544U 98067A   21275.52333333  .00001264  00000-0  29622-4 0  9993"
    _BASE_TLE2 = "2 25544  51.6442 213.5765 0003460 165.4960 194.6320 15.48916272305133"

    @staticmethod
    def _create_tle_with_inclination(norad_id: int, inclination_deg: float) -> tuple:
        """
        Create a valid TLE pair with a specific inclination value.
        Uses real TLE format and modifies only the inclination field.
        Returns (line1, line2) tuple.
        """
        # Modify line 1 to have the correct NORAD ID
        line1 = TestInclinationFilter._BASE_TLE1.replace("25544", f"{norad_id:5d}")
        
        # Modify line 2: replace NORAD ID and inclination
        # Position 0-7: "2 NORAD_ID "
        # Position 8-15: inclination (8 chars)
        # Position 16+: rest
        base_line2 = TestInclinationFilter._BASE_TLE2
        prefix = f"2 {norad_id:5d} "
        suffix = base_line2[16:]
        line2 = f"{prefix}{inclination_deg:8.4f}{suffix}"
        
        return line1, line2

    @settings(max_examples=100)
    @given(
        inc1=st.floats(min_value=0.0, max_value=180.0),
        inc2=st.floats(min_value=0.0, max_value=180.0),
    )
    def test_inclination_filter_accuracy(self, inc1, inc2):
        """
        Property 13: İnklinasyon Filtresi Doğruluğu
        
        For any two satellite pairs where inclination difference > 5 degrees,
        those pairs should be filtered out (not appear in conjunction analysis results).
        
        **Validates: Requirement 9.2**
        
        # Feature: orbitguard, Property 13: İnklinasyon Filtresi Doğruluğu
        """
        # Create TLE pairs with specific inclinations
        tle1_line1, tle1_line2 = self._create_tle_with_inclination(39522, inc1)
        tle2_line1, tle2_line2 = self._create_tle_with_inclination(40984, inc2)
        
        sat1 = {
            "name": "SAT1",
            "norad_id": 39522,
            "tle_line1": tle1_line1,
            "tle_line2": tle1_line2,
        }
        
        sat2 = {
            "name": "SAT2",
            "norad_id": 40984,
            "tle_line1": tle2_line1,
            "tle_line2": tle2_line2,
        }
        
        engine = ConjunctionEngine()
        
        # Calculate inclination difference
        inc_diff = abs(inc1 - inc2)
        
        # Call the inclination filter
        should_filter = engine._inclination_filter(sat1, sat2)
        
        # Verify filtering behavior:
        # - If inclination difference > 5°, the pair should be filtered (True)
        # - If inclination difference ≤ 5°, the pair should NOT be filtered (False)
        if inc_diff > 5.0:
            assert should_filter is True, (
                f"Pair with inclination diff {inc_diff:.4f}° (> 5°) should be filtered out"
            )
        else:
            assert should_filter is False, (
                f"Pair with inclination diff {inc_diff:.4f}° (≤ 5°) should NOT be filtered out"
            )


class TestMissDistanceField:
    """Property-based tests for conjunction miss distance field validity (P14)."""

    # Real TLE base lines (ISS)
    _BASE_TLE1 = "1 25544U 98067A   21275.52333333  .00001264  00000-0  29622-4 0  9993"
    _BASE_TLE2 = "2 25544  51.6442 213.5765 0003460 165.4960 194.6320 15.48916272305133"

    @staticmethod
    def _create_tle_pair(norad_id: int) -> tuple:
        """
        Create a valid TLE pair with a specific NORAD ID.
        Returns (line1, line2) tuple.
        """
        line1 = TestMissDistanceField._BASE_TLE1.replace("25544", f"{norad_id:5d}")
        line2 = TestMissDistanceField._BASE_TLE2.replace("25544", f"{norad_id:5d}")
        return line1, line2

    @settings(max_examples=100, deadline=None)
    @given(
        norad1=st.integers(min_value=10000, max_value=99999),
        norad2=st.integers(min_value=10000, max_value=99999),
    )
    def test_miss_distance_field_validity(self, norad1, norad2):
        """
        Property 14: Konjunksiyon Olayı Miss Distance Alanı
        
        For any conjunction analysis result, every conjunction event should have
        a miss_distance_km field and its value should be ≥ 0.
        
        **Validates: Requirement 9.3**
        
        # Feature: orbitguard, Property 14: Konjunksiyon Olayı Miss Distance Alanı
        """
        # Skip if same satellite
        if norad1 == norad2:
            return

        # Create TLE pairs
        tle1_line1, tle1_line2 = self._create_tle_pair(norad1)
        tle2_line1, tle2_line2 = self._create_tle_pair(norad2)

        sat1 = {
            "name": f"SAT_{norad1}",
            "norad_id": norad1,
            "tle_line1": tle1_line1,
            "tle_line2": tle1_line2,
        }

        sat2 = {
            "name": f"SAT_{norad2}",
            "norad_id": norad2,
            "tle_line1": tle2_line1,
            "tle_line2": tle2_line2,
        }

        engine = ConjunctionEngine()

        # Analyze the pair for conjunction events
        events = engine.analyze_pair(sat1, sat2, days=7)

        # Verify that every event has miss_distance_km field and it's >= 0
        for event in events:
            assert "miss_distance_km" in event, (
                f"Event missing 'miss_distance_km' field: {event}"
            )
            miss_dist = event["miss_distance_km"]
            assert isinstance(miss_dist, (int, float)), (
                f"miss_distance_km must be numeric, got {type(miss_dist)}"
            )
            assert miss_dist >= 0.0, (
                f"miss_distance_km must be >= 0, got {miss_dist}"
            )
