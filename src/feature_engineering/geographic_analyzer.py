"""
Geographic Analyzer Module

Calculates multi-radius population aggregations with area-weighted precision.
Uses state-specific Albers equal-area projections for accurate distance-based buffers.

CRITICAL IMPLEMENTATION NOTES:
1. Area-weighting prevents over-counting in sparse counties
2. State-specific CRS ensures accurate circular buffers (not ellipses)
3. Multi-radius approach (1, 3, 5, 10, 20 mi) based on trade area analysis

Author: Multi-State Dispensary Model - Phase 2
Date: October 2025
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import pygris
import warnings

# Suppress pygris warnings about cached data
warnings.filterwarnings('ignore', category=UserWarning, module='pygris')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GeographicAnalyzer:
    """
    Calculates area-weighted population within multiple radii.

    CRITICAL FEATURES (from Codex review):
    - Area-weighted population calculation (not whole-tract counts)
    - State-specific Albers projections for accurate buffers
    - Monotonic validation (pop_1mi <= pop_3mi <= ... <= pop_20mi)

    Trade area radii based on Insa Jacksonville data:
    - 1mi: Immediate local market
    - 3mi: Core trade area
    - 5mi: Extended local market
    - 10mi: Regional market
    - 20mi: Destination market (19% of visits from 30+ miles)
    """

    # Miles to meters conversion
    MILES_TO_METERS = 1609.34

    # Radii to calculate (based on trade area analysis)
    RADII_MILES = [1, 3, 5, 10, 20]

    # State-specific CRS (Albers equal-area projections)
    STATE_CRS = {
        'FL': 'EPSG:3086',  # Florida GDL Albers
        'PA': 'EPSG:6565'   # Pennsylvania Albers
    }

    # State FIPS codes for tract loading
    STATE_FIPS = {
        'FL': '12',
        'PA': '42'
    }

    def __init__(self, cache_dir: str = "data/census/tract_shapefiles"):
        """
        Initialize Geographic Analyzer.

        Args:
            cache_dir: Directory for caching tract shapefiles
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Will be loaded on first use
        self.fl_tracts = None
        self.pa_tracts = None

        logger.info("GeographicAnalyzer initialized")

    def _load_tracts(self, state: str) -> gpd.GeoDataFrame:
        """
        Load census tract boundaries for a state.

        Uses pygris to automatically download TIGER/Line shapefiles.

        Args:
            state: 'FL' or 'PA'

        Returns:
            GeoDataFrame with tract boundaries and precomputed areas
        """
        logger.info(f"Loading census tract boundaries for {state}")

        try:
            # Download tracts using pygris
            state_fips = self.STATE_FIPS[state]
            tracts_gdf = pygris.tracts(
                state=state_fips,
                year=2023,
                cache=True
            )

            # Ensure we have GEOID column
            if 'GEOID' not in tracts_gdf.columns:
                logger.error(f"GEOID column not found in {state} tracts")
                raise ValueError("Missing GEOID column")

            # Reproject to state-specific Albers CRS
            state_crs = self.STATE_CRS[state]
            tracts_gdf = tracts_gdf.to_crs(state_crs)

            # Precompute tract areas (in square meters)
            tracts_gdf['tract_area_sqm'] = tracts_gdf.geometry.area

            logger.info(f"Loaded {len(tracts_gdf)} tracts for {state} in {state_crs}")

            return tracts_gdf

        except Exception as e:
            logger.error(f"Failed to load tracts for {state}: {e}")
            raise

    def _ensure_tracts_loaded(self, state: str) -> None:
        """Ensure tract shapefiles are loaded for state."""
        if state == 'FL' and self.fl_tracts is None:
            self.fl_tracts = self._load_tracts('FL')
        elif state == 'PA' and self.pa_tracts is None:
            self.pa_tracts = self._load_tracts('PA')

    def _get_tracts_for_state(self, state: str) -> gpd.GeoDataFrame:
        """Get loaded tracts for state."""
        self._ensure_tracts_loaded(state)
        return self.fl_tracts if state == 'FL' else self.pa_tracts

    def create_buffer(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float,
        state: str
    ) -> Tuple[Polygon, str]:
        """
        Create accurate circular buffer around point.

        CRITICAL: Uses state-specific Albers projection for accurate distances.

        Steps:
        1. Create Point in WGS84 (EPSG:4326)
        2. Reproject to state-specific Albers equal-area CRS
        3. Buffer by radius in meters (miles × 1609.34)
        4. Return buffer geometry in processing CRS

        Args:
            latitude: Dispensary latitude (WGS84)
            longitude: Dispensary longitude (WGS84)
            radius_miles: Buffer radius in miles
            state: 'FL' or 'PA' for CRS selection

        Returns:
            Tuple of (buffer Polygon in Albers CRS, CRS string)
        """
        # Create point in WGS84
        point = Point(longitude, latitude)
        point_gdf = gpd.GeoDataFrame(
            {'geometry': [point]},
            crs='EPSG:4326'
        )

        # Reproject to state-specific Albers
        state_crs = self.STATE_CRS[state]
        point_gdf = point_gdf.to_crs(state_crs)

        # Create buffer in meters
        radius_meters = radius_miles * self.MILES_TO_METERS
        buffer = point_gdf.geometry[0].buffer(radius_meters)

        return buffer, state_crs

    def calculate_area_weighted_population(
        self,
        buffer: Polygon,
        tracts_gdf: gpd.GeoDataFrame,
        population_col: str = 'B01001_001E'
    ) -> Dict:
        """
        Calculate population using area-weighted intersection.

        CRITICAL: Prevents over-counting in sparse counties.

        Formula: population_in_buffer = tract_pop × (intersection_area ÷ tract_area)

        Args:
            buffer: Buffer polygon (in same CRS as tracts_gdf)
            tracts_gdf: Census tracts GeoDataFrame with population data
            population_col: Column name for population variable

        Returns:
            dict: {
                'total_population': float,
                'tract_count': int,
                'tracts': list[str],  # GEOIDs
                'weights': dict[str, float]  # GEOID -> proportion for debugging
            }
        """
        # Find intersecting tracts using spatial index (fast)
        buffer_gdf = gpd.GeoDataFrame({'geometry': [buffer]}, crs=tracts_gdf.crs)
        intersecting_tracts = gpd.sjoin(
            tracts_gdf,
            buffer_gdf,
            how='inner',
            predicate='intersects'
        )

        if len(intersecting_tracts) == 0:
            logger.warning("No tracts intersect buffer")
            return {
                'total_population': 0.0,
                'tract_count': 0,
                'tracts': [],
                'weights': {}
            }

        # Calculate area-weighted population
        total_population = 0.0
        tract_geoids = []
        tract_weights = {}

        for idx, tract in intersecting_tracts.iterrows():
            # Get tract population (handle missing data)
            tract_pop = tract.get(population_col, 0)
            if pd.isna(tract_pop):
                tract_pop = 0

            # Calculate intersection
            intersection = tract.geometry.intersection(buffer)
            intersection_area = intersection.area

            # Get tract total area
            tract_area = tract.get('tract_area_sqm', tract.geometry.area)

            # Calculate weight (proportion of tract inside buffer)
            weight = intersection_area / tract_area if tract_area > 0 else 0

            # Weight the population
            weighted_pop = tract_pop * weight

            total_population += weighted_pop

            # Store for debugging/validation
            geoid = tract.get('GEOID', 'unknown')
            tract_geoids.append(geoid)
            tract_weights[geoid] = weight

            logger.debug(f"Tract {geoid}: pop={tract_pop}, weight={weight:.3f}, "
                        f"weighted_pop={weighted_pop:.0f}")

        return {
            'total_population': total_population,
            'tract_count': len(intersecting_tracts),
            'tracts': tract_geoids,
            'weights': tract_weights
        }

    def calculate_multi_radius_population(
        self,
        latitude: float,
        longitude: float,
        state: str,
        tract_populations: gpd.GeoDataFrame
    ) -> Dict:
        """
        Calculate area-weighted population within 1, 3, 5, 10, 20 mile radii.

        Based on Insa trade area analysis showing ~19% of visits from 30+ miles.

        Implementation:
        1. Reproject point from WGS84 to state-specific Albers CRS
        2. Create buffers in planar CRS (accurate distance-based circles)
        3. Calculate area-weighted population for each buffer
        4. Validate monotonic increase (1mi <= 3mi <= ... <= 20mi)

        Args:
            latitude: Dispensary latitude (WGS84)
            longitude: Dispensary longitude (WGS84)
            state: 'FL' or 'PA'
            tract_populations: GeoDataFrame with population data by tract

        Returns:
            dict: {
                'pop_1mi': float,
                'pop_3mi': float,
                'pop_5mi': float,
                'pop_10mi': float,
                'pop_20mi': float,
                'tracts_1mi': list[str],
                'tracts_3mi': list[str],
                'tracts_5mi': list[str],
                'tracts_10mi': list[str],
                'tracts_20mi': list[str],
                'crs_used': str
            }
        """
        logger.debug(f"Calculating multi-radius population for {latitude}, {longitude} ({state})")

        # Ensure tracts are loaded
        self._ensure_tracts_loaded(state)

        # Get tracts for state
        tracts_gdf = self._get_tracts_for_state(state)

        # Merge population data into tracts
        # Assume tract_populations has GEOID and B01001_001E columns
        if 'B01001_001E' in tract_populations.columns:
            # Ensure GEOID is string type for both dataframes
            tracts_gdf_copy = tracts_gdf.copy()
            tracts_gdf_copy['GEOID'] = tracts_gdf_copy['GEOID'].astype(str)
            tract_pops_copy = tract_populations.copy()
            tract_pops_copy['GEOID'] = tract_pops_copy['GEOID'].astype(str)

            tracts_with_pop = tracts_gdf_copy.merge(
                tract_pops_copy[['GEOID', 'B01001_001E']],
                on='GEOID',
                how='left'
            )
        else:
            logger.warning("Population data not provided, using tract geometry only")
            tracts_with_pop = tracts_gdf.copy()
            tracts_with_pop['B01001_001E'] = 0

        # Calculate population for each radius
        result = {
            'crs_used': self.STATE_CRS[state]
        }

        for radius in self.RADII_MILES:
            # Create buffer
            buffer, crs = self.create_buffer(latitude, longitude, radius, state)

            # Calculate area-weighted population
            pop_data = self.calculate_area_weighted_population(
                buffer,
                tracts_with_pop,
                population_col='B01001_001E'
            )

            # Store results
            result[f'pop_{radius}mi'] = pop_data['total_population']
            result[f'tracts_{radius}mi'] = pop_data['tracts']

            logger.debug(f"{radius}mi buffer: {pop_data['total_population']:.0f} people "
                        f"({pop_data['tract_count']} tracts)")

        # Validate monotonic increase
        populations = [result[f'pop_{r}mi'] for r in self.RADII_MILES]
        is_monotonic = all(populations[i] <= populations[i+1] for i in range(len(populations)-1))

        if not is_monotonic:
            logger.warning(f"Population not monotonic for {latitude}, {longitude}: {populations}")

        return result

    def batch_calculate_populations(
        self,
        dispensaries_df: pd.DataFrame,
        demographics_df: pd.DataFrame,
        lat_col: str = 'latitude',
        lon_col: str = 'longitude',
        state_col: str = 'state_abbr'
    ) -> pd.DataFrame:
        """
        Calculate multi-radius populations for all dispensaries.

        Args:
            dispensaries_df: DataFrame with dispensary locations
            demographics_df: DataFrame with tract-level population data (GEOID, B01001_001E)
            lat_col: Latitude column name
            lon_col: Longitude column name
            state_col: State abbreviation column ('FL' or 'PA')

        Returns:
            DataFrame with added population columns
        """
        logger.info(f"Starting batch multi-radius population calculation for {len(dispensaries_df)} dispensaries")

        # Create copy
        result_df = dispensaries_df.copy()

        # Initialize population columns
        for radius in self.RADII_MILES:
            result_df[f'pop_{radius}mi'] = None

        # Convert demographics to GeoDataFrame (not spatial, just need GEOID and population)
        pop_lookup = demographics_df[['GEOID', 'B01001_001E']].copy() if 'B01001_001E' in demographics_df.columns else None

        # Process each dispensary
        for idx, row in result_df.iterrows():
            lat = row[lat_col]
            lon = row[lon_col]
            state = row[state_col]

            # Skip if missing coordinates or state
            if pd.isna(lat) or pd.isna(lon) or pd.isna(state):
                logger.warning(f"Missing coordinates or state for row {idx}")
                continue

            # Validate state
            if state not in ['FL', 'PA']:
                logger.warning(f"Invalid state '{state}' for row {idx}")
                continue

            try:
                # Calculate populations
                pop_data = self.calculate_multi_radius_population(
                    lat, lon, state, pop_lookup if pop_lookup is not None else pd.DataFrame()
                )

                # Update DataFrame
                for radius in self.RADII_MILES:
                    result_df.at[idx, f'pop_{radius}mi'] = pop_data[f'pop_{radius}mi']

            except Exception as e:
                logger.error(f"Error calculating populations for row {idx}: {e}")
                continue

            # Progress logging
            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(result_df)} dispensaries")

        logger.info("Multi-radius population calculation complete")
        return result_df


# Module test
if __name__ == "__main__":
    # Test with sample coordinates
    analyzer = GeographicAnalyzer()

    # Create sample population data
    sample_pop = pd.DataFrame({
        'GEOID': ['12086006713', '42101000500'],
        'B01001_001E': [1912, 3292]
    })

    # Miami test
    miami_pops = analyzer.calculate_multi_radius_population(
        25.761681, -80.191788, 'FL', sample_pop
    )
    print("\nMiami multi-radius populations:")
    for key, value in miami_pops.items():
        if key.startswith('pop_'):
            print(f"  {key}: {value:.0f}")
        elif key == 'crs_used':
            print(f"  {key}: {value}")

    # Philadelphia test
    philly_pops = analyzer.calculate_multi_radius_population(
        39.952583, -75.165222, 'PA', sample_pop
    )
    print("\nPhiladelphia multi-radius populations:")
    for key, value in philly_pops.items():
        if key.startswith('pop_'):
            print(f"  {key}: {value:.0f}")
        elif key == 'crs_used':
            print(f"  {key}: {value}")
