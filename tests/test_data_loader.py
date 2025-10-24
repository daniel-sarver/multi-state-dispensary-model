#!/usr/bin/env python3
"""
Data Loader Validation Tests

Validates that the MultiStateDataLoader correctly loads and provides
access to census and competition data for FL and PA.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.feature_engineering.data_loader import MultiStateDataLoader
from src.feature_engineering.exceptions import InvalidStateError


def test_initialization():
    """Test that data loader initializes correctly."""
    print("\n" + "=" * 70)
    print("TEST 1: Data Loader Initialization")
    print("=" * 70)

    loader = MultiStateDataLoader()

    # Check that all data is loaded
    assert loader.fl_dispensaries is not None, "FL dispensaries not loaded"
    assert loader.pa_dispensaries is not None, "PA dispensaries not loaded"
    assert loader.fl_census is not None, "FL census not loaded"
    assert loader.pa_census is not None, "PA census not loaded"
    assert loader.training_data is not None, "Training data not loaded"

    print("✅ PASS: All datasets loaded successfully")
    return loader


def test_data_counts(loader):
    """Test that data counts are reasonable."""
    print("\n" + "=" * 70)
    print("TEST 2: Data Count Validation")
    print("=" * 70)

    # Check dispensary counts
    fl_disp_count = len(loader.fl_dispensaries)
    pa_disp_count = len(loader.pa_dispensaries)
    total_disp = fl_disp_count + pa_disp_count

    print(f"Dispensaries:")
    print(f"  FL: {fl_disp_count}")
    print(f"  PA: {pa_disp_count}")
    print(f"  Total: {total_disp}")

    assert fl_disp_count > 0, "No FL dispensaries loaded"
    assert pa_disp_count > 0, "No PA dispensaries loaded"
    assert total_disp > 500, f"Total dispensaries ({total_disp}) seems low"

    # Check census counts
    fl_census_count = len(loader.fl_census)
    pa_census_count = len(loader.pa_census)
    total_census = fl_census_count + pa_census_count

    print(f"\nCensus Tracts:")
    print(f"  FL: {fl_census_count}")
    print(f"  PA: {pa_census_count}")
    print(f"  Total: {total_census}")

    assert fl_census_count > 0, "No FL census tracts loaded"
    assert pa_census_count > 0, "No PA census tracts loaded"

    # Phase 2 collected ~7,730 tracts statewide
    # After removing unpopulated tracts, should have 7,000+
    assert total_census >= 7000, f"Total census tracts ({total_census}) too low (expected ~7,600)"
    assert fl_census_count >= 4000, f"FL census tracts ({fl_census_count}) too low (expected ~5,000)"
    assert pa_census_count >= 2000, f"PA census tracts ({pa_census_count}) too low (expected ~2,600)"

    print("\n✅ PASS: Data counts are reasonable (statewide coverage)")


def test_required_columns(loader):
    """Test that required columns exist in loaded data."""
    print("\n" + "=" * 70)
    print("TEST 3: Required Columns Validation")
    print("=" * 70)

    # Check dispensary columns
    disp_required = ['state', 'latitude', 'longitude', 'regulator_name']
    fl_disp_cols = loader.fl_dispensaries.columns.tolist()

    for col in disp_required:
        assert col in fl_disp_cols, f"Missing dispensary column: {col}"

    print(f"✓ Dispensary data has all required columns: {disp_required}")

    # Check census columns
    census_required = [
        'state', 'census_geoid', 'census_state_fips', 'census_county_fips',
        'total_population', 'median_age', 'median_household_income',
        'population_density', 'tract_area_sqm'
    ]
    fl_census_cols = loader.fl_census.columns.tolist()

    for col in census_required:
        assert col in fl_census_cols, f"Missing census column: {col}"

    print(f"✓ Census data has all required columns: {census_required}")
    print(f"  Note: Census data uses GEOID for tract identification (no lat/lon centroids)")

    print("\n✅ PASS: All required columns present")


def test_coordinate_validity(loader):
    """Test that coordinates are within valid ranges."""
    print("\n" + "=" * 70)
    print("TEST 4: Coordinate Validity")
    print("=" * 70)

    # Check FL dispensary coordinates
    fl_lats = loader.fl_dispensaries['latitude']
    fl_lons = loader.fl_dispensaries['longitude']

    assert fl_lats.min() >= -90 and fl_lats.max() <= 90, "FL latitudes out of range"
    assert fl_lons.min() >= -180 and fl_lons.max() <= 180, "FL longitudes out of range"

    print(f"✓ FL dispensary coordinates valid:")
    print(f"    Lat range: {fl_lats.min():.4f} to {fl_lats.max():.4f}")
    print(f"    Lon range: {fl_lons.min():.4f} to {fl_lons.max():.4f}")

    # Check PA dispensary coordinates
    pa_lats = loader.pa_dispensaries['latitude']
    pa_lons = loader.pa_dispensaries['longitude']

    assert pa_lats.min() >= -90 and pa_lats.max() <= 90, "PA latitudes out of range"
    assert pa_lons.min() >= -180 and pa_lons.max() <= 180, "PA longitudes out of range"

    print(f"✓ PA dispensary coordinates valid:")
    print(f"    Lat range: {pa_lats.min():.4f} to {pa_lats.max():.4f}")
    print(f"    Lon range: {pa_lons.min():.4f} to {pa_lons.max():.4f}")

    # Check FL census GEOIDs
    fl_geoids = loader.fl_census['census_geoid']
    pa_geoids = loader.pa_census['census_geoid']

    assert fl_geoids.notna().all(), "FL census has missing GEOIDs"
    assert pa_geoids.notna().all(), "PA census has missing GEOIDs"

    print(f"✓ FL census GEOIDs valid: {len(fl_geoids)} unique tracts")
    print(f"✓ PA census GEOIDs valid: {len(pa_geoids)} unique tracts")
    print(f"  Note: Census tracts identified by GEOID, not coordinates")
    print(f"  Coordinate→Tract lookup uses Census Geocoding API")

    print("\n✅ PASS: All coordinates and GEOIDs are valid")


def test_state_data_retrieval(loader):
    """Test get_state_data() method."""
    print("\n" + "=" * 70)
    print("TEST 5: State Data Retrieval")
    print("=" * 70)

    # Test FL retrieval
    fl_disp, fl_census = loader.get_state_data('FL')
    assert len(fl_disp) > 0, "FL dispensaries not returned"
    assert len(fl_census) > 0, "FL census not returned"
    print(f"✓ FL data retrieved: {len(fl_disp)} dispensaries, {len(fl_census)} tracts")

    # Test PA retrieval
    pa_disp, pa_census = loader.get_state_data('PA')
    assert len(pa_disp) > 0, "PA dispensaries not returned"
    assert len(pa_census) > 0, "PA census not returned"
    print(f"✓ PA data retrieved: {len(pa_disp)} dispensaries, {len(pa_census)} tracts")

    # Test case insensitivity
    fl_disp_lower, _ = loader.get_state_data('fl')
    assert len(fl_disp_lower) == len(fl_disp), "Case insensitivity failed"
    print("✓ Case insensitive retrieval works")

    print("\n✅ PASS: State data retrieval working correctly")


def test_error_handling(loader):
    """Test that invalid states raise appropriate errors."""
    print("\n" + "=" * 70)
    print("TEST 6: Error Handling")
    print("=" * 70)

    # Test invalid state
    try:
        loader.get_state_data('CA')
        assert False, "Should have raised InvalidStateError for CA"
    except InvalidStateError as e:
        print(f"✓ InvalidStateError raised for CA: {e}")

    # Test another invalid state
    try:
        loader.get_state_data('NY')
        assert False, "Should have raised InvalidStateError for NY"
    except InvalidStateError as e:
        print(f"✓ InvalidStateError raised for NY: {e}")

    print("\n✅ PASS: Error handling working correctly")


def test_data_summary(loader):
    """Test data summary generation."""
    print("\n" + "=" * 70)
    print("TEST 7: Data Summary")
    print("=" * 70)

    summary = loader.get_data_summary()

    assert 'states_supported' in summary, "Missing states_supported in summary"
    assert 'total_dispensaries' in summary, "Missing total_dispensaries in summary"
    assert 'total_census_tracts' in summary, "Missing total_census_tracts in summary"
    assert 'by_state' in summary, "Missing by_state in summary"

    print(f"✓ Summary structure correct")
    print(f"  States: {summary['states_supported']}")
    print(f"  Total Dispensaries: {summary['total_dispensaries']}")
    print(f"  Total Census Tracts: {summary['total_census_tracts']}")

    print("\n✅ PASS: Data summary generation working")


def test_demographics_data_quality(loader):
    """Test that demographics data is present and reasonable."""
    print("\n" + "=" * 70)
    print("TEST 8: Demographics Data Quality")
    print("=" * 70)

    # Check FL census demographics
    fl_pop = loader.fl_census['total_population']
    assert fl_pop.notna().all(), "FL has missing population values"
    assert fl_pop.min() > 0, "FL has zero or negative population"
    print(f"✓ FL population data valid:")
    print(f"    Range: {fl_pop.min():,.0f} to {fl_pop.max():,.0f}")
    print(f"    Mean: {fl_pop.mean():,.0f}")

    # Check PA census demographics
    pa_pop = loader.pa_census['total_population']
    assert pa_pop.notna().all(), "PA has missing population values"
    assert pa_pop.min() > 0, "PA has zero or negative population"
    print(f"✓ PA population data valid:")
    print(f"    Range: {pa_pop.min():,.0f} to {pa_pop.max():,.0f}")
    print(f"    Mean: {pa_pop.mean():,.0f}")

    # Check median age
    fl_age = loader.fl_census['median_age']
    assert fl_age.min() > 0 and fl_age.max() < 100, "FL age data out of reasonable range"
    print(f"✓ FL median age data valid: {fl_age.min():.1f} to {fl_age.max():.1f}")

    print("\n✅ PASS: Demographics data quality is good")


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("MULTI-STATE DATA LOADER VALIDATION SUITE")
    print("=" * 70)

    try:
        # Test 1: Initialization
        loader = test_initialization()

        # Test 2: Data counts
        test_data_counts(loader)

        # Test 3: Required columns
        test_required_columns(loader)

        # Test 4: Coordinate validity
        test_coordinate_validity(loader)

        # Test 5: State data retrieval
        test_state_data_retrieval(loader)

        # Test 6: Error handling
        test_error_handling(loader)

        # Test 7: Data summary
        test_data_summary(loader)

        # Test 8: Demographics quality
        test_demographics_data_quality(loader)

        # All tests passed
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Data Loader is Production Ready")
        print("=" * 70)
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
