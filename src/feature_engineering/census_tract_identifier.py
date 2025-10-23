"""
Census Tract Identifier Module

Converts dispensary coordinates (latitude/longitude) to census tract FIPS codes
using the US Census Bureau Geocoding API.

Author: Multi-State Dispensary Model - Phase 2
Date: October 2025
"""

import requests
import pandas as pd
import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CensusTractIdentifier:
    """
    Identifies census tract FIPS codes from latitude/longitude coordinates.

    Uses the Census Geocoding API (free, no key required) to convert
    dispensary coordinates to census tract identifiers.

    Features:
    - Batch processing with progress tracking
    - Automatic retry with exponential backoff
    - Caching to avoid redundant API calls
    - Comprehensive error handling
    - Checkpoint saving for crash recovery
    """

    def __init__(self, cache_dir: str = "data/census/cache"):
        """
        Initialize Census Tract Identifier.

        Args:
            cache_dir: Directory for caching geocoding results
        """
        self.geocoding_url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
        self.session = requests.Session()  # Connection pooling

        # Set up caching
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "geocoding_cache.json"
        self.cache = self._load_cache()

        logger.info(f"CensusTractIdentifier initialized with cache at {self.cache_file}")

    def _load_cache(self) -> Dict:
        """Load cached geocoding results from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached geocoding results")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                return {}
        return {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved cache with {len(self.cache)} entries")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _make_cache_key(self, latitude: float, longitude: float) -> str:
        """
        Create cache key from coordinates.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            Cache key string
        """
        # Round to 6 decimal places (~0.1m precision) for cache matching
        return f"{latitude:.6f},{longitude:.6f}"

    def get_tract_from_coordinates(
        self,
        latitude: float,
        longitude: float,
        max_retries: int = 3
    ) -> Dict:
        """
        Get census tract FIPS code from coordinates.

        Args:
            latitude: Latitude in decimal degrees (WGS84)
            longitude: Longitude in decimal degrees (WGS84)
            max_retries: Maximum number of retry attempts

        Returns:
            dict: {
                'state_fips': str (2 digits),
                'county_fips': str (3 digits),
                'tract_fips': str (6 digits),
                'geoid': str (11 digits - state+county+tract),
                'tract_name': str,
                'success': bool,
                'error': Optional[str]
            }
        """
        # Check cache first
        cache_key = self._make_cache_key(latitude, longitude)
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]

        # Prepare API parameters
        params = {
            'x': longitude,
            'y': latitude,
            'benchmark': '4',  # Public_AR_Current
            'vintage': '4',    # Current_Current
            'format': 'json'
        }

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                logger.debug(f"Geocoding {latitude}, {longitude} (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(
                    self.geocoding_url,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()

                # Parse response
                result = self._parse_geocoding_response(data, latitude, longitude)

                # Cache successful results
                if result['success']:
                    self.cache[cache_key] = result
                    self._save_cache()

                return result

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {latitude}, {longitude}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                else:
                    return {
                        'state_fips': None,
                        'county_fips': None,
                        'tract_fips': None,
                        'geoid': None,
                        'tract_name': None,
                        'success': False,
                        'error': 'API timeout after retries'
                    }

            except Exception as e:
                logger.error(f"Error geocoding {latitude}, {longitude}: {e}")
                return {
                    'state_fips': None,
                    'county_fips': None,
                    'tract_fips': None,
                    'geoid': None,
                    'tract_name': None,
                    'success': False,
                    'error': str(e)
                }

    def _parse_geocoding_response(
        self,
        data: Dict,
        latitude: float,
        longitude: float
    ) -> Dict:
        """
        Parse Census Geocoding API response.

        Args:
            data: JSON response from API
            latitude: Original latitude
            longitude: Original longitude

        Returns:
            Parsed result dictionary
        """
        try:
            # Navigate response structure
            result = data.get('result', {})
            geographies = result.get('geographies', {})
            census_tracts = geographies.get('Census Tracts', [])

            if not census_tracts:
                logger.warning(f"No census tract found for {latitude}, {longitude}")
                return {
                    'state_fips': None,
                    'county_fips': None,
                    'tract_fips': None,
                    'geoid': None,
                    'tract_name': None,
                    'success': False,
                    'error': 'No census tract found'
                }

            # Extract first tract (should only be one)
            tract = census_tracts[0]

            return {
                'state_fips': tract.get('STATE'),
                'county_fips': tract.get('COUNTY'),
                'tract_fips': tract.get('TRACT'),
                'geoid': tract.get('GEOID'),
                'tract_name': tract.get('BASENAME'),
                'success': True,
                'error': None
            }

        except Exception as e:
            logger.error(f"Error parsing geocoding response: {e}")
            return {
                'state_fips': None,
                'county_fips': None,
                'tract_fips': None,
                'geoid': None,
                'tract_name': None,
                'success': False,
                'error': f'Parse error: {str(e)}'
            }

    def batch_identify_tracts(
        self,
        df: pd.DataFrame,
        lat_col: str = 'latitude',
        lon_col: str = 'longitude',
        checkpoint_file: str = "data/census/intermediate/tracts_identified.csv",
        checkpoint_interval: int = 50
    ) -> pd.DataFrame:
        """
        Add census tract identifiers to dispensary dataframe.

        Args:
            df: DataFrame with dispensary coordinates
            lat_col: Name of latitude column
            lon_col: Name of longitude column
            checkpoint_file: File for saving intermediate results
            checkpoint_interval: Save checkpoint every N records

        Returns:
            DataFrame with added census tract columns:
            - census_state_fips
            - census_county_fips
            - census_tract_fips
            - census_geoid
            - census_tract_name
            - census_tract_error (bool flag)
        """
        logger.info(f"Starting batch census tract identification for {len(df)} dispensaries")

        # Create copy to avoid modifying original
        result_df = df.copy()

        # Initialize new columns
        result_df['census_state_fips'] = None
        result_df['census_county_fips'] = None
        result_df['census_tract_fips'] = None
        result_df['census_geoid'] = None
        result_df['census_tract_name'] = None
        result_df['census_tract_error'] = False

        # Check for existing checkpoint
        checkpoint_path = Path(checkpoint_file)
        start_idx = 0

        if checkpoint_path.exists():
            logger.info(f"Found checkpoint file: {checkpoint_file}")
            try:
                checkpoint_df = pd.read_csv(checkpoint_file)
                # Count successful identifications in checkpoint
                completed = checkpoint_df['census_geoid'].notna().sum()
                logger.info(f"Resuming from checkpoint with {completed} tracts already identified")
                result_df = checkpoint_df
                start_idx = len(checkpoint_df)
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}. Starting from beginning.")

        # Process each row
        success_count = 0
        error_count = 0

        for idx, row in result_df.iterrows():
            # Skip already processed rows
            if idx < start_idx:
                if pd.notna(row['census_geoid']):
                    success_count += 1
                continue

            # Get coordinates
            lat = row[lat_col]
            lon = row[lon_col]

            # Skip if coordinates are missing
            if pd.isna(lat) or pd.isna(lon):
                result_df.at[idx, 'census_tract_error'] = True
                error_count += 1
                logger.warning(f"Missing coordinates for row {idx}")
                continue

            # Geocode
            tract_info = self.get_tract_from_coordinates(lat, lon)

            # Update DataFrame
            if tract_info['success']:
                result_df.at[idx, 'census_state_fips'] = tract_info['state_fips']
                result_df.at[idx, 'census_county_fips'] = tract_info['county_fips']
                result_df.at[idx, 'census_tract_fips'] = tract_info['tract_fips']
                result_df.at[idx, 'census_geoid'] = tract_info['geoid']
                result_df.at[idx, 'census_tract_name'] = tract_info['tract_name']
                result_df.at[idx, 'census_tract_error'] = False
                success_count += 1
            else:
                result_df.at[idx, 'census_tract_error'] = True
                error_count += 1
                logger.warning(f"Failed to geocode row {idx}: {tract_info['error']}")

            # Progress logging
            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} dispensaries "
                           f"({success_count} success, {error_count} errors)")

            # Checkpoint saving
            if (idx + 1) % checkpoint_interval == 0:
                logger.info(f"Saving checkpoint at row {idx + 1}")
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                result_df.to_csv(checkpoint_file, index=False)

            # Rate limiting (be respectful to Census API)
            time.sleep(0.2)  # 5 requests per second max

        # Final save
        logger.info("Saving final results")
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(checkpoint_file, index=False)

        # Summary
        logger.info(f"Census tract identification complete:")
        logger.info(f"  Total: {len(df)}")
        logger.info(f"  Success: {success_count} ({success_count/len(df)*100:.1f}%)")
        logger.info(f"  Errors: {error_count} ({error_count/len(df)*100:.1f}%)")

        return result_df


# Module test
if __name__ == "__main__":
    # Test with sample coordinates
    identifier = CensusTractIdentifier()

    # Miami, FL test
    miami_result = identifier.get_tract_from_coordinates(25.761681, -80.191788)
    print("Miami test:", miami_result)

    # Philadelphia, PA test
    philly_result = identifier.get_tract_from_coordinates(39.952583, -75.165222)
    print("Philadelphia test:", philly_result)
