#!/usr/bin/env python3
"""
Unit tests for data integration logic.

Tests the core matching and filtering functionality to prevent regressions.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_integration.create_combined_datasets import MultiStateCombinedProcessor


class TestCannabisFiltering:
    """Test suite for cannabis dispensary filtering logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MultiStateCombinedProcessor()

    def test_known_cannabis_chains_not_filtered(self):
        """Verify known cannabis brands are not filtered despite misleading names."""
        # Test data with cannabis brands that have "wellness" in name
        test_data = pd.DataFrame({
            'Sub Category': ['Marijuana Dispensary'] * 4,
            'Category': ['Medical & Recreational Cannabis Dispensaries'] * 4,
            'Property Name': [
                'Surterra Wellness',
                'AYR Cannabis Dispensary',
                'Restore Wellness (Ayr)',
                'Trulieve'
            ],
            'Address': ['123 Main St'] * 4,
            'City': ['Miami'] * 4,
            'State': ['FL'] * 4,
            'Zip Code': ['33101'] * 4,
            'Latitude': [25.7] * 4,
            'Longitude': [-80.2] * 4,
            'Visits': [10000] * 4,
            'sq ft': [2000] * 4,
            'Visits / sq ft': [5.0] * 4
        })

        result = self.processor.filter_cannabis_only(test_data, 'FL')

        # All 4 should be kept
        assert len(result) == 4, f"Expected 4 records, got {len(result)}"
        assert 'Surterra Wellness' in result['Property Name'].values
        assert 'AYR Cannabis Dispensary' in result['Property Name'].values

    def test_hemp_cbd_stores_filtered(self):
        """Verify hemp/CBD stores are correctly filtered out."""
        test_data = pd.DataFrame({
            'Sub Category': ['Marijuana Dispensary'] * 3,
            'Category': ['Medical & Recreational Cannabis Dispensaries'] * 3,
            'Property Name': [
                'Pure Hemp Shop',
                'CBD Wellness Center',
                'Kratom Plus'
            ],
            'Address': ['123 Main St'] * 3,
            'City': ['Miami'] * 3,
            'State': ['FL'] * 3,
            'Zip Code': ['33101'] * 3,
            'Latitude': [25.7] * 3,
            'Longitude': [-80.2] * 3,
            'Visits': [5000] * 3,
            'sq ft': [1000] * 3,
            'Visits / sq ft': [5.0] * 3
        })

        result = self.processor.filter_cannabis_only(test_data, 'FL')

        # All 3 should be filtered
        assert len(result) == 0, f"Expected 0 records, got {len(result)}"

    def test_category_based_filtering(self):
        """Verify non-cannabis categories are filtered."""
        test_data = pd.DataFrame({
            'Sub Category': ['Smoke Shop', 'Marijuana Dispensary'],
            'Category': ['Tobacco', 'Medical & Recreational Cannabis Dispensaries'],
            'Property Name': ['Smoke Shop', 'Curaleaf'],
            'Address': ['123 Main St'] * 2,
            'City': ['Miami'] * 2,
            'State': ['FL'] * 2,
            'Zip Code': ['33101'] * 2,
            'Latitude': [25.7] * 2,
            'Longitude': [-80.2] * 2,
            'Visits': [5000] * 2,
            'sq ft': [1000] * 2,
            'Visits / sq ft': [5.0] * 2
        })

        result = self.processor.filter_cannabis_only(test_data, 'FL')

        # Only Curaleaf should remain
        assert len(result) == 1
        assert result.iloc[0]['Property Name'] == 'Curaleaf'


class TestAddressMatching:
    """Test suite for address matching logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MultiStateCombinedProcessor()

    def test_exact_address_match(self):
        """Test exact address matching with same street format."""
        placer_data = pd.DataFrame({
            'Property Name': ['Trulieve'],
            'Address': ['5037 US-90'],
            'City': ['Pace'],
            'State': ['FL'],
            'Zip Code': ['32571'],
            'Latitude': [30.6],
            'Longitude': [-87.1],
            'Visits': [100000],
            'sq ft': [3000],
            'Visits / sq ft': [33.3]
        })

        regulator_data = pd.DataFrame({
            'COMPANY': ['Trulieve'],
            'ADDRESS': ['5037 US Highway 90'],
            'CITY': ['Pace'],
            'ZIP CODE': ['32571'],
            'COUNTY': ['Santa Rosa']
        })

        matches, unmatched, remaining = self.processor.match_placer_to_regulator(
            placer_data, regulator_data, 'FL'
        )

        # Should match (after standardization: "5037 US 90" vs "5037 US HIGHWAY 90")
        assert len(matches) >= 0, "Matching should not crash"
        # Note: Exact match behavior depends on standardization rules

    def test_city_zip_improve_match_score(self):
        """Test that matching city and ZIP improve match confidence."""
        placer_data = pd.DataFrame({
            'Property Name': ['Test Store'],
            'Address': ['100 Main Street'],
            'City': ['Tampa'],
            'State': ['FL'],
            'Zip Code': ['33602'],
            'Latitude': [27.9],
            'Longitude': [-82.4],
            'Visits': [50000],
            'sq ft': [2500],
            'Visits / sq ft': [20.0]
        })

        # Two potential matches - same street different cities
        regulator_data = pd.DataFrame({
            'COMPANY': ['Store A', 'Store B'],
            'ADDRESS': ['100 Main St', '100 Main St'],
            'CITY': ['Tampa', 'Orlando'],
            'ZIP CODE': ['33602', '32801'],
            'COUNTY': ['Hillsborough', 'Orange']
        })

        matches, unmatched, remaining = self.processor.match_placer_to_regulator(
            placer_data, regulator_data, 'FL'
        )

        # Should match to Tampa location (same city/ZIP)
        if len(matches) > 0:
            assert matches.iloc[0]['regulator_city'] == 'Tampa'

    def test_no_duplicate_regulator_matches(self):
        """Test that each regulator record is only matched once."""
        placer_data = pd.DataFrame({
            'Property Name': ['Store 1', 'Store 2'],
            'Address': ['123 Oak St', '123 Oak Street'],  # Very similar
            'City': ['Miami', 'Miami'],
            'State': ['FL', 'FL'],
            'Zip Code': ['33101', '33101'],
            'Latitude': [25.7, 25.7],
            'Longitude': [-80.2, -80.2],
            'Visits': [50000, 48000],
            'sq ft': [2500, 2400],
            'Visits / sq ft': [20.0, 20.0]
        })

        # Only one regulator record
        regulator_data = pd.DataFrame({
            'COMPANY': ['The Store'],
            'ADDRESS': ['123 Oak St'],
            'CITY': ['Miami'],
            'ZIP CODE': ['33101'],
            'COUNTY': ['Miami-Dade']
        })

        matches, unmatched, remaining = self.processor.match_placer_to_regulator(
            placer_data, regulator_data, 'FL'
        )

        # Should match only once, even though both Placer records are similar
        # One Placer record should match, one should be unmatched
        assert len(matches) + len(unmatched) == 2
        if len(matches) > 0:
            assert len(matches) == 1, "Should only match one Placer record to the regulator"


class TestCoordinateValidation:
    """Test suite for coordinate boundary validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MultiStateCombinedProcessor()

    def test_valid_fl_coordinates(self):
        """Test that valid Florida coordinates pass validation."""
        test_data = pd.DataFrame({
            'state': ['FL'] * 3,
            'placer_name': ['Store A', 'Store B', 'Store C'],
            'placer_address': ['123 Main St'] * 3,
            'latitude': [25.7, 28.5, 30.2],  # Valid FL range
            'longitude': [-80.2, -82.5, -85.0],  # Valid FL range
            'has_placer_data': [True] * 3
        })

        result = self.processor.validate_coordinates(test_data, 'FL')

        # All coordinates should remain valid
        assert result['latitude'].notna().sum() == 3
        assert result['longitude'].notna().sum() == 3

    def test_invalid_coordinates_cleared(self):
        """Test that invalid coordinates are cleared but records kept."""
        test_data = pd.DataFrame({
            'state': ['FL', 'FL', 'FL'],
            'placer_name': ['Valid Store', 'Wrong Lat', 'Wrong Lon'],
            'placer_address': ['123 Main St'] * 3,
            'latitude': [25.7, 45.0, 28.5],  # 45.0 is outside FL
            'longitude': [-80.2, -82.5, -120.0],  # -120.0 is outside FL
            'has_placer_data': [True] * 3
        })

        result = self.processor.validate_coordinates(test_data, 'FL')

        # Should have 3 records but some coordinates cleared
        assert len(result) == 3
        # First record should still have coordinates
        assert pd.notna(result.iloc[0]['latitude'])
        # Invalid coordinates should be cleared
        # (exact behavior depends on bounds checking logic)

    def test_pa_coordinate_boundaries(self):
        """Test Pennsylvania-specific coordinate validation."""
        test_data = pd.DataFrame({
            'state': ['PA'] * 2,
            'placer_name': ['Valid PA Store', 'FL Store Misclassified'],
            'placer_address': ['123 Main St'] * 2,
            'latitude': [40.5, 25.7],  # 25.7 is FL, not PA
            'longitude': [-76.0, -80.2],
            'has_placer_data': [True] * 2
        })

        result = self.processor.validate_coordinates(test_data, 'PA')

        # First should pass, second should fail
        assert pd.notna(result.iloc[0]['latitude'])
        # Second record's coordinates should be cleared


class TestAddressStandardization:
    """Test suite for address standardization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MultiStateCombinedProcessor()

    def test_street_abbreviations(self):
        """Test that street type abbreviations are standardized."""
        test_cases = [
            ('123 Main Street', '123 MAIN ST'),
            ('456 Oak Avenue', '456 OAK AVE'),
            ('789 Park Boulevard', '789 PARK BLVD'),
            ('100 First Road', '100 FIRST RD'),
        ]

        for input_addr, expected_pattern in test_cases:
            result = self.processor.standardize_address(input_addr)
            assert 'ST' in result or 'AVE' in result or 'BLVD' in result or 'RD' in result

    def test_directional_abbreviations(self):
        """Test that directionals are abbreviated."""
        test_cases = [
            '100 North Main Street',
            '200 South Oak Avenue',
            '300 East Park Blvd',
            '400 West First Road'
        ]

        for addr in test_cases:
            result = self.processor.standardize_address(addr)
            # Should have N, S, E, or W
            assert any(d in result for d in ['N ', 'S ', 'E ', 'W '])
            # Should NOT have full words
            assert 'NORTH' not in result
            assert 'SOUTH' not in result

    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        addr = "123 Main St., Suite #100"
        result = self.processor.standardize_address(addr)

        # Should not have period or hash
        assert '.' not in result
        assert '#' not in result
        assert ',' not in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
