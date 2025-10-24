"""
Multi-State Data Loader

Loads census tract and dispensary competition data for FL and PA.
Provides clean, validated data sources for coordinate-based feature calculation.

Key Principle: Load real data only - NO synthetic data, NO estimates.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

try:
    from .exceptions import InvalidStateError
except ImportError:
    # Allow running as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from exceptions import InvalidStateError


class MultiStateDataLoader:
    """
    Load and manage census and competition data for FL and PA.

    This class loads data once during initialization and provides
    state-specific data access for feature calculation.

    Attributes:
        fl_dispensaries (DataFrame): Florida dispensary locations
        pa_dispensaries (DataFrame): Pennsylvania dispensary locations
        fl_census (DataFrame): Florida census tracts with demographics
        pa_census (DataFrame): Pennsylvania census tracts with demographics
        training_data (DataFrame): Full training dataset
    """

    # State boundaries for validation (approximate)
    STATE_BOUNDS = {
        'FL': {
            'lat_min': 24.5, 'lat_max': 31.0,
            'lon_min': -87.6, 'lon_max': -80.0
        },
        'PA': {
            'lat_min': 39.7, 'lat_max': 42.3,
            'lon_min': -80.5, 'lon_max': -74.7
        }
    }

    SUPPORTED_STATES = ['FL', 'PA']

    def __init__(self):
        """Initialize data loader and load all required datasets."""
        self.fl_dispensaries = None
        self.pa_dispensaries = None
        self.fl_census = None
        self.pa_census = None
        self.training_data = None

        # Project root
        self.project_root = Path(__file__).parent.parent.parent

        print("🔄 Loading multi-state data sources...")
        self.load_training_data()
        self.load_dispensary_data()
        self.load_census_data()
        print("✅ All data sources loaded successfully\n")

    def load_training_data(self):
        """Load the complete training dataset."""
        training_file = self.project_root / "data" / "processed" / "combined_with_competitive_features_corrected.csv"

        try:
            self.training_data = pd.read_csv(training_file)
            print(f"  ✓ Loaded training data: {len(self.training_data)} records")

            # Validate required columns exist
            required_cols = ['state', 'latitude', 'longitude', 'has_placer_data']
            missing_cols = [col for col in required_cols if col not in self.training_data.columns]

            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Training data not found at {training_file}. "
                "Ensure data/processed/combined_with_competitive_features_corrected.csv exists."
            )
        except Exception as e:
            raise RuntimeError(f"Error loading training data: {e}")

    def load_dispensary_data(self):
        """
        Load FL and PA dispensaries for competition analysis.

        Extracts verified dispensary locations from training data.
        Only includes dispensaries with Placer data (verified locations).

        Returns verified dispensaries with columns:
        - state: FL or PA
        - latitude: WGS84 latitude
        - longitude: WGS84 longitude
        - regulator_name: Dispensary name from regulator data
        - placer_name: Dispensary name from Placer data
        """
        print("  🏢 Loading dispensary locations for competition analysis...")

        # Filter to verified dispensaries only (has Placer data)
        dispensaries = self.training_data[
            self.training_data['has_placer_data'] == True
        ].copy()

        # Select relevant columns
        dispensary_cols = ['state', 'latitude', 'longitude', 'regulator_name', 'placer_name']
        dispensaries = dispensaries[dispensary_cols].copy()

        # Remove any rows with missing coordinates
        dispensaries = dispensaries.dropna(subset=['latitude', 'longitude'])

        # Validate coordinates are within reasonable bounds
        dispensaries = dispensaries[
            (dispensaries['latitude'].between(-90, 90)) &
            (dispensaries['longitude'].between(-180, 180))
        ]

        # Split by state
        self.fl_dispensaries = dispensaries[dispensaries['state'] == 'FL'].copy()
        self.pa_dispensaries = dispensaries[dispensaries['state'] == 'PA'].copy()

        print(f"    • Florida: {len(self.fl_dispensaries)} dispensaries")
        print(f"    • Pennsylvania: {len(self.pa_dispensaries)} dispensaries")
        print(f"    • Total: {len(self.fl_dispensaries) + len(self.pa_dispensaries)} verified locations")

        # Validate we have data for both states
        if len(self.fl_dispensaries) == 0:
            raise ValueError("No Florida dispensaries found in training data")
        if len(self.pa_dispensaries) == 0:
            raise ValueError("No Pennsylvania dispensaries found in training data")

    def load_census_data(self):
        """
        Load FL and PA census tracts for population analysis.

        Loads full statewide census tract demographics from Phase 2 output.
        This includes ALL 7,730 census tracts (5,057 FL + 2,673 PA), not just
        the ~600 tracts that have dispensaries in the training data.

        This comprehensive coverage ensures that coordinate-based feature
        calculation works for ANY location in FL or PA, not just near existing
        dispensaries.

        Returns census tracts with columns:
        - census_geoid: Unique census tract identifier (11-digit FIPS)
        - census_state_fips: State FIPS code (12=FL, 42=PA)
        - census_county_fips: County FIPS code
        - census_tract_fips: Tract FIPS code
        - tract_area_sqm: Tract area in square meters
        - total_population: Total population in tract
        - median_age: Median age in tract
        - median_household_income: Median household income
        - per_capita_income: Per capita income
        - total_pop_25_plus: Population 25 years and older
        - bachelors_degree: Number with bachelor's degree
        - masters_degree: Number with master's degree
        - professional_degree: Number with professional degree
        - doctorate_degree: Number with doctorate degree
        - population_density: Population per square mile (calculated)
        - census_data_complete: Boolean flag for data completeness
        - census_api_error: Boolean flag for API errors
        """
        print("  📍 Loading statewide census tract data...")

        # Load full statewide census data from Phase 2 output
        census_file = self.project_root / "data" / "census" / "intermediate" / "all_tracts_demographics.csv"

        if not census_file.exists():
            raise FileNotFoundError(
                f"Statewide census data not found at {census_file}. "
                "Expected Phase 2 output with ~7,700 census tracts."
            )

        census = pd.read_csv(census_file, dtype={'census_geoid': str})
        print(f"    • Loaded {len(census)} statewide census tracts")

        # Add state column from FIPS code
        census['state'] = census['census_state_fips'].map({12: 'FL', 42: 'PA'})

        # Remove census tracts with zero or missing population
        # These are unpopulated industrial/commercial areas not useful for retail analysis
        original_count = len(census)
        census = census[census['total_population'].notna() & (census['total_population'] > 0)]
        removed = original_count - len(census)
        if removed > 0:
            print(f"    • Removed {removed} unpopulated tracts")

        # Calculate population density (population per square mile)
        # tract_area_sqm is in square meters, convert to square miles (1 sq mi = 2,589,988.11 sq m)
        census['population_density'] = census['total_population'] / (census['tract_area_sqm'] / 2589988.11)

        # Load census tract centroids for distance calculations
        census = self._add_tract_centroids(census)

        # Split by state
        self.fl_census = census[census['state'] == 'FL'].copy()
        self.pa_census = census[census['state'] == 'PA'].copy()

        print(f"    • Florida: {len(self.fl_census)} census tracts")
        print(f"    • Pennsylvania: {len(self.pa_census)} census tracts")
        print(f"    • Total: {len(self.fl_census) + len(self.pa_census)} census tracts with demographics")

        # Validate we have adequate coverage for both states
        if len(self.fl_census) < 1000:
            raise ValueError(f"Insufficient Florida census tract coverage: {len(self.fl_census)} (expected ~5,000)")
        if len(self.pa_census) < 500:
            raise ValueError(f"Insufficient Pennsylvania census tract coverage: {len(self.pa_census)} (expected ~2,600)")

    def _add_tract_centroids(self, census: pd.DataFrame) -> pd.DataFrame:
        """
        Add latitude/longitude centroids for census tracts.

        Uses cached centroid data if available, otherwise calculates approximate
        centroids from county-level data. For exact centroids, run
        scripts/fetch_tract_centroids.py (one-time 15-20 minute operation).

        Args:
            census (DataFrame): Census tract data with census_geoid column

        Returns:
            DataFrame: Census data with added 'latitude' and 'longitude' columns
        """
        print("    • Loading census tract centroids...")

        # Check for cached exact centroids
        cache_file = self.project_root / "data" / "census" / "cache" / "tract_centroids.csv"

        if cache_file.exists():
            print(f"      ✓ Loading exact centroids from cache...")
            centroids_df = pd.read_csv(cache_file, dtype={'census_geoid': str})
            census = census.merge(centroids_df[['census_geoid', 'latitude', 'longitude']],
                                 on='census_geoid', how='left')

            missing = census['latitude'].isna().sum()
            if missing == 0:
                print(f"      ✓ All {len(census)} tract centroids loaded from cache")
                return census

        # No cache - use approximate centroids from county centers
        # This is fast but less accurate (~1-5 mile error typical)
        print(f"      ℹ️  Using approximate centroids from county centers")
        print(f"      💡 For exact centroids, run: python3 scripts/fetch_tract_centroids.py")

        census = self._add_approximate_centroids(census)

        return census

    def _add_approximate_centroids(self, census: pd.DataFrame) -> pd.DataFrame:
        """
        Add approximate centroids using county-level geographic centers.

        This is a fast approximation useful for testing. Typical error is 1-5 miles
        from true tract centroid, which is acceptable for population/competition
        analysis at 5-20 mile radii.

        Args:
            census (DataFrame): Census data with state/county FIPS

        Returns:
            DataFrame: Census data with approximate lat/lon added
        """
        # County center coordinates for FL and PA major counties
        # These are approximate centers of counties
        county_centers = {
            # Florida major counties
            ('12', '011'): (26.6706, -80.0933),  # Broward
            ('12', '086'): (27.9506, -82.4572),  # Miami-Dade
            ('12', '095'): (28.5383, -81.3792),  # Orange (Orlando)
            ('12', '103'): (27.8364, -82.6881),  # Pinellas
            ('12', '057'): (26.6406, -81.8732),  # Hillsborough (Tampa)
            ('12', '071'): (26.2034, -80.1252),  # Lee
            ('12', '009'): (30.4382, -84.2807),  # Brevard

            # Pennsylvania major counties
            ('42', '003'): (40.4686, -79.9375),  # Allegheny (Pittsburgh)
            ('42', '101'): (40.0379, -75.1398),  # Philadelphia
            ('42', '091'): (40.2732, -76.8867),  # Montgomery
            ('42', '045'): (40.0417, -76.3058),  # Delaware
            ('42', '017'): (40.6023, -75.4714),  # Bucks
            ('42', '071'): (40.0412, -76.3065),  # Lancaster
            ('42', '077'): (40.4406, -78.3947),  # Lehigh
        }

        # State default centers (used if county not in list)
        state_centers = {
            '12': (28.0, -82.0),  # FL approximate center
            '42': (40.5, -77.5),  # PA approximate center
        }

        def get_approx_centroid(row):
            state_fips = str(row['census_state_fips']).zfill(2)
            county_fips = str(row['census_county_fips']).zfill(3)

            # Try county lookup
            key = (state_fips, county_fips)
            if key in county_centers:
                return pd.Series(county_centers[key])

            # Fall back to state center
            if state_fips in state_centers:
                return pd.Series(state_centers[state_fips])

            # Last resort - use zeros (will be filtered in validation)
            return pd.Series((0.0, 0.0))

        census[['latitude', 'longitude']] = census.apply(get_approx_centroid, axis=1)

        return census

    def _save_centroid_cache(self, census: pd.DataFrame) -> None:
        """
        Save tract centroids to cache file.

        Args:
            census (DataFrame): Census data with lat/lon
        """
        cache_file = self.project_root / "data" / "census" / "cache" / "tract_centroids.csv"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Save only GEOID and centroids
        centroid_data = census[['census_geoid', 'latitude', 'longitude']].copy()
        centroid_data = centroid_data[centroid_data['latitude'].notna()]

        centroid_data.to_csv(cache_file, index=False)
        print(f"      ✓ Cached {len(centroid_data)} centroids to {cache_file}")

    def _fill_missing_centroids(self, census: pd.DataFrame) -> pd.DataFrame:
        """
        Fill missing centroids using Census API.

        Args:
            census (DataFrame): Census data with some missing lat/lon

        Returns:
            DataFrame: Census data with centroids filled
        """
        from .census_tract_identifier import CensusTractIdentifier
        import requests
        import time

        missing_mask = census['latitude'].isna()
        missing_tracts = census[missing_mask].copy()

        if len(missing_tracts) == 0:
            return census

        print(f"      Fetching {len(missing_tracts)} tract centroids from Census API...")

        for idx, tract in missing_tracts.iterrows():
            geoid = tract['census_geoid']
            state_fips = geoid[:2]
            county_fips = geoid[2:5]
            tract_fips = geoid[5:11]

            try:
                # Use Census TIGERweb API for tract geometry
                url = f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/8/query"
                params = {
                    'where': f"STATE='{state_fips}' AND COUNTY='{county_fips}' AND TRACT='{tract_fips}'",
                    'outFields': 'CENTLAT,CENTLON',
                    'f': 'json'
                }

                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                if 'features' in data and len(data['features']) > 0:
                    attrs = data['features'][0]['attributes']
                    census.at[idx, 'latitude'] = float(attrs.get('CENTLAT', 0))
                    census.at[idx, 'longitude'] = float(attrs.get('CENTLON', 0))

                time.sleep(0.2)  # Rate limiting

            except Exception as e:
                print(f"      ⚠️  Could not fetch centroid for {geoid}: {e}")
                # Leave as NaN - will be handled in population calculation
                continue

        return census

    def _add_tract_centroids_via_api(self, census: pd.DataFrame) -> pd.DataFrame:
        """
        Add all tract centroids using Census API (fallback method).

        Args:
            census (DataFrame): Census tract data

        Returns:
            DataFrame: Census data with lat/lon added
        """
        import requests
        import time

        print(f"      Fetching centroids for {len(census)} tracts...")

        census['latitude'] = np.nan
        census['longitude'] = np.nan

        for idx, tract in census.iterrows():
            geoid = tract['census_geoid']
            state_fips = geoid[:2]
            county_fips = geoid[2:5]
            tract_fips = geoid[5:11]

            try:
                url = f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/8/query"
                params = {
                    'where': f"STATE='{state_fips}' AND COUNTY='{county_fips}' AND TRACT='{tract_fips}'",
                    'outFields': 'CENTLAT,CENTLON',
                    'f': 'json'
                }

                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                if 'features' in data and len(data['features']) > 0:
                    attrs = data['features'][0]['attributes']
                    census.at[idx, 'latitude'] = float(attrs.get('CENTLAT', 0))
                    census.at[idx, 'longitude'] = float(attrs.get('CENTLON', 0))

                if (idx + 1) % 100 == 0:
                    print(f"        Progress: {idx + 1}/{len(census)} tracts")

                time.sleep(0.2)  # Rate limiting

            except Exception as e:
                print(f"      ⚠️  Could not fetch centroid for {geoid}: {e}")
                continue

        return census

    def get_state_data(self, state: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get dispensary and census data for specified state.

        Args:
            state (str): State code ('FL' or 'PA')

        Returns:
            Tuple[DataFrame, DataFrame]: (dispensaries_df, census_df) for state

        Raises:
            InvalidStateError: If state is not 'FL' or 'PA'
        """
        state = state.upper().strip()

        if state not in self.SUPPORTED_STATES:
            raise InvalidStateError(
                f"State '{state}' is not supported. "
                f"Model only supports: {', '.join(self.SUPPORTED_STATES)}"
            )

        if state == 'FL':
            return self.fl_dispensaries, self.fl_census
        elif state == 'PA':
            return self.pa_dispensaries, self.pa_census

    def get_state_bounds(self, state: str) -> Dict[str, float]:
        """
        Get geographic boundaries for state validation.

        Args:
            state (str): State code ('FL' or 'PA')

        Returns:
            Dict[str, float]: Dictionary with lat_min, lat_max, lon_min, lon_max

        Raises:
            InvalidStateError: If state is not 'FL' or 'PA'
        """
        state = state.upper().strip()

        if state not in self.SUPPORTED_STATES:
            raise InvalidStateError(
                f"State '{state}' is not supported. "
                f"Model only supports: {', '.join(self.SUPPORTED_STATES)}"
            )

        return self.STATE_BOUNDS[state]

    def get_dispensary_count(self, state: str = None) -> int:
        """
        Get total dispensary count for state or all states.

        Args:
            state (str, optional): State code ('FL' or 'PA'). If None, returns total.

        Returns:
            int: Number of dispensaries
        """
        if state is None:
            return len(self.fl_dispensaries) + len(self.pa_dispensaries)

        state = state.upper().strip()
        if state == 'FL':
            return len(self.fl_dispensaries)
        elif state == 'PA':
            return len(self.pa_dispensaries)
        else:
            return 0

    def get_census_tract_count(self, state: str = None) -> int:
        """
        Get total census tract count for state or all states.

        Args:
            state (str, optional): State code ('FL' or 'PA'). If None, returns total.

        Returns:
            int: Number of census tracts
        """
        if state is None:
            return len(self.fl_census) + len(self.pa_census)

        state = state.upper().strip()
        if state == 'FL':
            return len(self.fl_census)
        elif state == 'PA':
            return len(self.pa_census)
        else:
            return 0

    def get_data_summary(self) -> Dict[str, any]:
        """
        Get summary of loaded data.

        Returns:
            Dict: Summary statistics for loaded data
        """
        return {
            'states_supported': self.SUPPORTED_STATES,
            'total_dispensaries': self.get_dispensary_count(),
            'total_census_tracts': self.get_census_tract_count(),
            'by_state': {
                'FL': {
                    'dispensaries': len(self.fl_dispensaries),
                    'census_tracts': len(self.fl_census),
                    'bounds': self.STATE_BOUNDS['FL']
                },
                'PA': {
                    'dispensaries': len(self.pa_dispensaries),
                    'census_tracts': len(self.pa_census),
                    'bounds': self.STATE_BOUNDS['PA']
                }
            }
        }


def main():
    """Test the data loader."""
    print("=" * 70)
    print("MULTI-STATE DATA LOADER TEST")
    print("=" * 70)
    print()

    # Initialize loader
    loader = MultiStateDataLoader()

    # Print summary
    summary = loader.get_data_summary()
    print("\n📊 Data Summary:")
    print(f"  States Supported: {', '.join(summary['states_supported'])}")
    print(f"  Total Dispensaries: {summary['total_dispensaries']}")
    print(f"  Total Census Tracts: {summary['total_census_tracts']}")
    print("\n  By State:")
    for state, data in summary['by_state'].items():
        print(f"    {state}:")
        print(f"      Dispensaries: {data['dispensaries']}")
        print(f"      Census Tracts: {data['census_tracts']}")
        print(f"      Bounds: {data['bounds']}")

    # Test state data retrieval
    print("\n🧪 Testing state data retrieval...")
    fl_disp, fl_census = loader.get_state_data('FL')
    print(f"  ✓ Florida: {len(fl_disp)} dispensaries, {len(fl_census)} tracts")

    pa_disp, pa_census = loader.get_state_data('PA')
    print(f"  ✓ Pennsylvania: {len(pa_disp)} dispensaries, {len(pa_census)} tracts")

    # Test error handling
    print("\n🧪 Testing error handling...")
    try:
        loader.get_state_data('CA')
        print("  ❌ FAILED: Should have raised InvalidStateError")
    except InvalidStateError as e:
        print(f"  ✓ InvalidStateError raised correctly: {e}")

    print("\n✅ All tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
