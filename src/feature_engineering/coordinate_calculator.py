"""
Coordinate-Based Feature Calculator

Automatically calculates all 23 base features from coordinates (latitude, longitude).
This eliminates the need for users to manually input population, competition, and
demographic data - the system calculates everything automatically.

Key Features:
- Population calculation at 1, 3, 5, 10, 20 mile radii
- Competitor counts at same radii
- Distance-weighted competition score
- Census tract matching and demographic extraction
- Master method generating all 23 features from coordinates

Author: Multi-State Dispensary Model - Phase 2 CLI Automation
Date: October 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
from geopy.distance import geodesic
import warnings
warnings.filterwarnings('ignore')

try:
    from .data_loader import MultiStateDataLoader
    from .census_tract_identifier import CensusTractIdentifier
    from .exceptions import DataNotFoundError, InvalidStateError, InvalidCoordinatesError
except ImportError:
    # Allow running as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import MultiStateDataLoader
    from census_tract_identifier import CensusTractIdentifier
    from exceptions import DataNotFoundError, InvalidStateError, InvalidCoordinatesError


class CoordinateFeatureCalculator:
    """
    Calculate all 23 base features from coordinates.

    This class takes user-provided coordinates and automatically generates:
    - 5 population features (1mi, 3mi, 5mi, 10mi, 20mi radii)
    - 10 competition features (5 counts + 5 normalized + 1 weighted)
    - 7 demographic features from census tract
    - 1 optional square footage feature

    Total: 23 base features ready for feature_validator transformation.

    Attributes:
        data_loader (MultiStateDataLoader): Loads census and dispensary data
        census_identifier (CensusTractIdentifier): Census API wrapper

    Key Principle: NO FALLBACK VALUES
    - If data is unavailable, raise explicit DataNotFoundError
    - Never use default values or estimates
    - Users must know when data is missing
    """

    # Analysis radii in miles
    RADII = [1, 3, 5, 10, 20]

    # State median square footages (for when user doesn't provide)
    STATE_MEDIAN_SQ_FT = {
        'FL': 3500,  # Median FL dispensary size from training data
        'PA': 4000   # Median PA dispensary size from training data
    }

    def __init__(self, data_loader: MultiStateDataLoader = None):
        """
        Initialize coordinate feature calculator.

        Args:
            data_loader (MultiStateDataLoader, optional): Pre-loaded data loader.
                If None, creates new instance (loads 7,624 census tracts + 741 dispensaries).
        """
        print("🔄 Initializing Coordinate Feature Calculator...")

        # Load data if not provided
        if data_loader is None:
            self.data_loader = MultiStateDataLoader()
        else:
            self.data_loader = data_loader

        # Initialize Census API wrapper
        self.census_identifier = CensusTractIdentifier()

        print("✅ Feature calculator ready\n")

    def validate_coordinates(self, state: str, latitude: float, longitude: float) -> None:
        """
        Validate that coordinates are reasonable and within state bounds.

        Args:
            state (str): State code ('FL' or 'PA')
            latitude (float): Latitude in decimal degrees
            longitude (float): Longitude in decimal degrees

        Raises:
            InvalidCoordinatesError: If coordinates are invalid or outside state bounds
        """
        # Basic coordinate validation
        if not -90 <= latitude <= 90:
            raise InvalidCoordinatesError(
                f"Invalid latitude: {latitude}. Must be between -90 and 90."
            )

        if not -180 <= longitude <= 180:
            raise InvalidCoordinatesError(
                f"Invalid longitude: {longitude}. Must be between -180 and 180."
            )

        # Check state boundaries (approximate, for sanity check)
        bounds = self.data_loader.get_state_bounds(state)

        if not (bounds['lat_min'] <= latitude <= bounds['lat_max']):
            raise InvalidCoordinatesError(
                f"Latitude {latitude} is outside {state} boundaries "
                f"({bounds['lat_min']:.2f} to {bounds['lat_max']:.2f}). "
                f"Verify coordinates are in {state}."
            )

        if not (bounds['lon_min'] <= longitude <= bounds['lon_max']):
            raise InvalidCoordinatesError(
                f"Longitude {longitude} is outside {state} boundaries "
                f"({bounds['lon_min']:.2f} to {bounds['lon_max']:.2f}). "
                f"Verify coordinates are in {state}."
            )

    def calculate_population_multi_radius(
        self,
        state: str,
        latitude: float,
        longitude: float
    ) -> Dict[str, int]:
        """
        Calculate total population within 1, 3, 5, 10, and 20 mile radii.

        Sums population from all census tracts whose centroids fall within
        each radius. Uses geodesic (Haversine) distance for accuracy.

        Args:
            state (str): State code ('FL' or 'PA')
            latitude (float): Latitude in decimal degrees
            longitude (float): Longitude in decimal degrees

        Returns:
            dict: {
                'pop_1mi': int,
                'pop_3mi': int,
                'pop_5mi': int,
                'pop_10mi': int,
                'pop_20mi': int
            }

        Raises:
            InvalidStateError: If state is not FL or PA
            InvalidCoordinatesError: If coordinates are invalid
        """
        # Validate inputs
        state = state.upper().strip()
        self.validate_coordinates(state, latitude, longitude)

        # Get census data for state
        _, census_df = self.data_loader.get_state_data(state)

        # Calculate distance from target coordinates to each census tract
        target_coords = (latitude, longitude)

        # Calculate distances to all tracts
        distances = []
        for _, tract in census_df.iterrows():
            tract_coords = (tract['latitude'], tract['longitude'])
            distance_miles = geodesic(target_coords, tract_coords).miles
            distances.append(distance_miles)

        census_df = census_df.copy()
        census_df['distance_miles'] = distances

        # Calculate population within each radius
        populations = {}
        for radius in self.RADII:
            tracts_within_radius = census_df[census_df['distance_miles'] <= radius]
            total_pop = tracts_within_radius['total_population'].sum()
            populations[f'pop_{radius}mi'] = int(total_pop)

        return populations

    def calculate_competitors_multi_radius(
        self,
        state: str,
        latitude: float,
        longitude: float
    ) -> Dict[str, int]:
        """
        Count competitor dispensaries within 1, 3, 5, 10, and 20 mile radii.

        Counts verified dispensary locations within each radius.
        Excludes self (any dispensary within 0.1 miles is considered same location).

        Args:
            state (str): State code ('FL' or 'PA')
            latitude (float): Latitude in decimal degrees
            longitude (float): Longitude in decimal degrees

        Returns:
            dict: {
                'competitors_1mi': int,
                'competitors_3mi': int,
                'competitors_5mi': int,
                'competitors_10mi': int,
                'competitors_20mi': int,
                'competitors_per_100k_1mi': float,
                'competitors_per_100k_3mi': float,
                'competitors_per_100k_5mi': float,
                'competitors_per_100k_10mi': float,
                'competitors_per_100k_20mi': float
            }

        Raises:
            InvalidStateError: If state is not FL or PA
            InvalidCoordinatesError: If coordinates are invalid
        """
        # Validate inputs
        state = state.upper().strip()
        self.validate_coordinates(state, latitude, longitude)

        # Get dispensary and census data for state
        dispensaries_df, _ = self.data_loader.get_state_data(state)

        # Calculate distance from target coordinates to each dispensary
        target_coords = (latitude, longitude)

        distances = []
        for _, disp in dispensaries_df.iterrows():
            disp_coords = (disp['latitude'], disp['longitude'])
            distance_miles = geodesic(target_coords, disp_coords).miles
            distances.append(distance_miles)

        dispensaries_df = dispensaries_df.copy()
        dispensaries_df['distance_miles'] = distances

        # Exclude self (within 0.1 miles)
        dispensaries_df = dispensaries_df[dispensaries_df['distance_miles'] > 0.1]

        # Count competitors within each radius
        competitors = {}

        # First get populations for normalization
        populations = self.calculate_population_multi_radius(state, latitude, longitude)

        for radius in self.RADII:
            # Count competitors
            count = len(dispensaries_df[dispensaries_df['distance_miles'] <= radius])
            competitors[f'competitors_{radius}mi'] = count

            # Calculate competitors per 100k population
            pop_key = f'pop_{radius}mi'
            population = populations[pop_key]

            if population > 0:
                per_100k = (count / population) * 100000
            else:
                per_100k = 0.0

            competitors[f'competitors_per_100k_{radius}mi'] = per_100k

        return competitors

    def calculate_competition_weighted(
        self,
        state: str,
        latitude: float,
        longitude: float,
        radius: float = 20
    ) -> float:
        """
        Calculate distance-weighted competition score.

        Closer competitors have more impact. Formula:
        score = sum(1 / (distance + 0.01)) for all competitors within radius

        The +0.01 prevents division by zero for very close competitors.

        Args:
            state (str): State code ('FL' or 'PA')
            latitude (float): Latitude in decimal degrees
            longitude (float): Longitude in decimal degrees
            radius (float): Analysis radius in miles (default: 20)

        Returns:
            float: Distance-weighted competition score

        Raises:
            InvalidStateError: If state is not FL or PA
            InvalidCoordinatesError: If coordinates are invalid
        """
        # Validate inputs
        state = state.upper().strip()
        self.validate_coordinates(state, latitude, longitude)

        # Get dispensary data for state
        dispensaries_df, _ = self.data_loader.get_state_data(state)

        # Calculate distance from target coordinates to each dispensary
        target_coords = (latitude, longitude)

        distances = []
        for _, disp in dispensaries_df.iterrows():
            disp_coords = (disp['latitude'], disp['longitude'])
            distance_miles = geodesic(target_coords, disp_coords).miles
            distances.append(distance_miles)

        dispensaries_df = dispensaries_df.copy()
        dispensaries_df['distance_miles'] = distances

        # Exclude self and filter to radius
        dispensaries_df = dispensaries_df[
            (dispensaries_df['distance_miles'] > 0.1) &
            (dispensaries_df['distance_miles'] <= radius)
        ]

        # Calculate weighted score
        if len(dispensaries_df) == 0:
            return 0.0

        weighted_score = sum(1 / (d + 0.01) for d in dispensaries_df['distance_miles'])

        return weighted_score

    def match_census_tract(
        self,
        state: str,
        latitude: float,
        longitude: float
    ) -> Dict[str, any]:
        """
        Find census tract for coordinates and extract demographic features.

        Uses Census Geocoding API to identify the exact census tract containing
        the coordinates, then looks up demographics from loaded census data.

        Args:
            state (str): State code ('FL' or 'PA')
            latitude (float): Latitude in decimal degrees
            longitude (float): Longitude in decimal degrees

        Returns:
            dict: {
                'census_geoid': str,
                'median_age': float,
                'median_household_income': float,
                'per_capita_income': float,
                'pct_bachelors_or_higher': float,
                'population_density': float,
                'tract_area_sqm': float,
                'tract_total_population': int
            }

        Raises:
            DataNotFoundError: If census tract not found or demographics unavailable
            InvalidStateError: If state is not FL or PA
            InvalidCoordinatesError: If coordinates are invalid
        """
        # Validate inputs
        state = state.upper().strip()
        self.validate_coordinates(state, latitude, longitude)

        # Call Census Geocoding API
        print(f"  📍 Looking up census tract for ({latitude:.4f}, {longitude:.4f})...")
        tract_info = self.census_identifier.get_tract_from_coordinates(latitude, longitude)

        if not tract_info['success']:
            raise DataNotFoundError(
                f"❌ Census tract lookup failed for coordinates ({latitude:.4f}, {longitude:.4f})\n"
                f"Error: {tract_info['error']}\n\n"
                f"This means we cannot determine demographic data for this location.\n"
                f"Possible causes:\n"
                f"  • Coordinates are in water or unpopulated area\n"
                f"  • Coordinates are outside US boundaries\n"
                f"  • Census API is temporarily unavailable\n\n"
                f"Cannot proceed without census demographic data."
            )

        geoid = tract_info['geoid']
        print(f"    ✓ Found census tract: {geoid}")

        # Look up demographics in loaded census data
        _, census_df = self.data_loader.get_state_data(state)

        tract_data = census_df[census_df['census_geoid'] == geoid]

        if len(tract_data) == 0:
            raise DataNotFoundError(
                f"❌ Census tract {geoid} not found in {state} demographics database\n\n"
                f"The Census API identified this tract, but we don't have demographic\n"
                f"data for it in our database. This should not happen if coordinates\n"
                f"are within {state}.\n\n"
                f"Verify:\n"
                f"  • Coordinates are within {state} boundaries\n"
                f"  • Census data file has complete coverage\n\n"
                f"Cannot proceed without census demographic data."
            )

        tract = tract_data.iloc[0]

        # Extract demographic features
        # Return raw census features as expected by feature_validator
        demographics = {
            'census_geoid': geoid,
            'median_age': float(tract['median_age']),
            'median_household_income': float(tract['median_household_income']),
            'per_capita_income': float(tract['per_capita_income']),
            'population_density': float(tract['population_density']),
            'tract_area_sqm': float(tract['tract_area_sqm']),
            # Raw census demographics (as expected by feature_validator)
            'total_population': int(tract['total_population']),
            'total_pop_25_plus': int(tract['total_pop_25_plus']),
            'bachelors_degree': int(tract['bachelors_degree']),
            'masters_degree': int(tract['masters_degree']),
            'professional_degree': int(tract['professional_degree']),
            'doctorate_degree': int(tract['doctorate_degree'])
        }

        print(f"    ✓ Demographics extracted")

        return demographics

    def calculate_all_features(
        self,
        state: str,
        latitude: float,
        longitude: float,
        sq_ft: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Calculate all 23 base features from coordinates.

        This is the master method that generates everything needed for
        model prediction from just 3-4 user inputs.

        Args:
            state (str): State code ('FL' or 'PA')
            latitude (float): Latitude in decimal degrees
            longitude (float): Longitude in decimal degrees
            sq_ft (float, optional): Store square footage.
                If not provided, uses state median.

        Returns:
            dict: All 23 base features ready for feature_validator:
                - 5 population features (pop_1mi through pop_20mi)
                - 10 competition features (competitors and normalized)
                - 1 weighted competition feature
                - 7 demographic features
                - 1 square footage feature (optional)

        Raises:
            DataNotFoundError: If required data unavailable
            InvalidStateError: If state not supported
            InvalidCoordinatesError: If coordinates invalid
        """
        print(f"\n{'='*70}")
        print(f"🎯 Calculating Features for {state} Location")
        print(f"{'='*70}")
        print(f"Coordinates: ({latitude:.6f}, {longitude:.6f})")

        # Validate state
        state = state.upper().strip()
        if state not in ['FL', 'PA']:
            raise InvalidStateError(
                f"State '{state}' is not supported. "
                f"Model only supports FL (Florida) and PA (Pennsylvania)."
            )

        # Validate coordinates
        self.validate_coordinates(state, latitude, longitude)
        print(f"✓ Coordinates validated")

        # Calculate population features
        print(f"\n📊 Calculating population features...")
        populations = self.calculate_population_multi_radius(state, latitude, longitude)
        for radius in self.RADII:
            pop = populations[f'pop_{radius}mi']
            print(f"  • {radius}mi radius: {pop:,} people")

        # Calculate competition features
        print(f"\n🏢 Calculating competition features...")
        competitors = self.calculate_competitors_multi_radius(state, latitude, longitude)
        for radius in self.RADII:
            count = competitors[f'competitors_{radius}mi']
            per_100k = competitors[f'competitors_per_100k_{radius}mi']
            print(f"  • {radius}mi radius: {count} competitors ({per_100k:.2f} per 100k)")

        # Calculate weighted competition
        print(f"\n⚖️  Calculating distance-weighted competition...")
        competition_weighted = self.calculate_competition_weighted(state, latitude, longitude, radius=20)
        print(f"  • Weighted score (20mi): {competition_weighted:.4f}")

        # Match census tract and get demographics
        print(f"\n🗺️  Matching census tract and extracting demographics...")
        demographics = self.match_census_tract(state, latitude, longitude)
        print(f"  • Census tract: {demographics['census_geoid']}")
        print(f"  • Median age: {demographics['median_age']:.1f} years")
        print(f"  • Median household income: ${demographics['median_household_income']:,.0f}")
        print(f"  • Per capita income: ${demographics['per_capita_income']:,.0f}")
        print(f"  • Total population: {demographics['total_population']:,}")
        print(f"  • Population density: {demographics['population_density']:,.1f} per sq mi")

        # Handle square footage
        if sq_ft is None:
            sq_ft = self.STATE_MEDIAN_SQ_FT[state]
            print(f"\n📐 Using state median square footage: {sq_ft:,} sq ft")
        else:
            print(f"\n📐 Using provided square footage: {sq_ft:,} sq ft")

        # Combine all features
        all_features = {
            # Core identifiers
            'state': state,
            'latitude': latitude,
            'longitude': longitude,
            'sq_ft': sq_ft,

            # Population features (5)
            'pop_1mi': populations['pop_1mi'],
            'pop_3mi': populations['pop_3mi'],
            'pop_5mi': populations['pop_5mi'],
            'pop_10mi': populations['pop_10mi'],
            'pop_20mi': populations['pop_20mi'],

            # Competition count features (5)
            'competitors_1mi': competitors['competitors_1mi'],
            'competitors_3mi': competitors['competitors_3mi'],
            'competitors_5mi': competitors['competitors_5mi'],
            'competitors_10mi': competitors['competitors_10mi'],
            'competitors_20mi': competitors['competitors_20mi'],

            # Normalized competition features (5) - NOT required by feature_validator
            'competitors_per_100k_1mi': competitors['competitors_per_100k_1mi'],
            'competitors_per_100k_3mi': competitors['competitors_per_100k_3mi'],
            'competitors_per_100k_5mi': competitors['competitors_per_100k_5mi'],
            'competitors_per_100k_10mi': competitors['competitors_per_100k_10mi'],
            'competitors_per_100k_20mi': competitors['competitors_per_100k_20mi'],

            # Weighted competition feature (1)
            'competition_weighted_20mi': competition_weighted,

            # Demographic features (11) - as required by feature_validator
            'census_geoid': demographics['census_geoid'],
            'median_age': demographics['median_age'],
            'median_household_income': demographics['median_household_income'],
            'per_capita_income': demographics['per_capita_income'],
            'population_density': demographics['population_density'],
            'tract_area_sqm': demographics['tract_area_sqm'],
            'total_population': demographics['total_population'],
            'total_pop_25_plus': demographics['total_pop_25_plus'],
            'bachelors_degree': demographics['bachelors_degree'],
            'masters_degree': demographics['masters_degree'],
            'professional_degree': demographics['professional_degree'],
            'doctorate_degree': demographics['doctorate_degree']
        }

        print(f"\n{'='*70}")
        print(f"✅ Feature Calculation Complete")
        print(f"{'='*70}")
        print(f"Total features generated: {len(all_features)}")
        print(f"  • Population features: 5")
        print(f"  • Competition features: 11 (5 counts + 5 normalized + 1 weighted)")
        print(f"  • Demographic features: 7")
        print(f"  • Store size: 1")
        print(f"\nReady for feature_validator transformation (23 → 44 features)")

        return all_features


# Module test
if __name__ == "__main__":
    print("Testing Coordinate Feature Calculator\n")

    # Initialize calculator
    calculator = CoordinateFeatureCalculator()

    # Test with Insa Orlando coordinates (known location from training data)
    print("\n" + "="*70)
    print("TEST: Insa Orlando, FL")
    print("="*70)

    try:
        features = calculator.calculate_all_features(
            state='FL',
            latitude=28.5685,
            longitude=-81.2163,
            sq_ft=3500
        )

        print("\n✅ Test completed successfully")
        print(f"\nSample features:")
        print(f"  • pop_5mi: {features['pop_5mi']:,}")
        print(f"  • competitors_5mi: {features['competitors_5mi']}")
        print(f"  • median_age: {features['median_age']:.1f}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
