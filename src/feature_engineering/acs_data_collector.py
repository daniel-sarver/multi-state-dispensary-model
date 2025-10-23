"""
ACS Data Collector Module

Fetches demographic variables from the US Census Bureau American Community Survey (ACS)
5-Year API at the census tract level.

Author: Multi-State Dispensary Model - Phase 2
Date: October 2025
"""

import os
import requests
import pandas as pd
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ACSDataCollector:
    """
    Collects demographic variables from ACS 5-Year API.

    Fetches population, age, income, and education data at the census tract level
    using the Census Bureau API.

    Features:
    - Secure API key management (environment variables)
    - Batch processing with rate limiting
    - Caching to minimize API calls
    - Comprehensive error handling
    - Missing value detection and flagging
    """

    # ACS variable codes
    ACS_VARIABLES = {
        'B01001_001E': 'total_population',
        'B01002_001E': 'median_age',
        'B19013_001E': 'median_household_income',
        'B19301_001E': 'per_capita_income',
        'B15003_001E': 'total_pop_25_plus',
        'B15003_022E': 'bachelors_degree',
        'B15003_023E': 'masters_degree',
        'B15003_024E': 'professional_degree',
        'B15003_025E': 'doctorate_degree'
    }

    # Census missing value codes
    MISSING_VALUE_CODES = [-666666666, -888888888, -999999999]

    def __init__(self, cache_dir: str = "data/census/cache"):
        """
        Initialize ACS Data Collector.

        Args:
            cache_dir: Directory for caching ACS results

        Raises:
            ValueError: If CENSUS_API_KEY environment variable not set
        """
        # Retrieve API key from environment (NEVER hard-code)
        self.api_key = os.environ.get("CENSUS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CENSUS_API_KEY environment variable not set. "
                "Set it with: export CENSUS_API_KEY=your_key_here"
            )

        self.base_url = "https://api.census.gov/data/2023/acs/acs5"
        self.session = requests.Session()  # Connection pooling

        # Set up caching
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "acs_cache.json"
        self.cache = self._load_cache()

        logger.info(f"ACSDataCollector initialized with cache at {self.cache_file}")
        logger.info(f"API key configured (ends with ...{self.api_key[-4:]})")

    def _load_cache(self) -> Dict:
        """Load cached ACS results from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached ACS results")
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

    def _clean_value(self, value: any) -> Optional[float]:
        """
        Clean ACS value, converting missing codes to None.

        Args:
            value: Raw value from ACS API

        Returns:
            Cleaned value or None if missing
        """
        if value is None:
            return None

        try:
            numeric_value = float(value)
            if numeric_value in self.MISSING_VALUE_CODES:
                return None
            return numeric_value
        except (ValueError, TypeError):
            return None

    def get_tract_demographics(
        self,
        state_fips: str,
        county_fips: str,
        tract_fips: str,
        max_retries: int = 3
    ) -> Dict:
        """
        Fetch demographic variables for a single census tract.

        Args:
            state_fips: 2-digit state FIPS code
            county_fips: 3-digit county FIPS code
            tract_fips: 6-digit tract FIPS code
            max_retries: Maximum number of retry attempts

        Returns:
            dict: {
                'geoid': str,
                'total_population': float,
                'median_age': float,
                'median_household_income': float,
                'per_capita_income': float,
                'total_pop_25_plus': float,
                'bachelors_degree': float,
                'masters_degree': float,
                'professional_degree': float,
                'doctorate_degree': float,
                'success': bool,
                'error': Optional[str],
                'data_complete': bool
            }
        """
        # Create GEOID for caching
        geoid = f"{state_fips}{county_fips}{tract_fips}"

        # Check cache
        if geoid in self.cache:
            logger.debug(f"Cache hit for GEOID {geoid}")
            return self.cache[geoid]

        # Prepare API request
        variables = ','.join(self.ACS_VARIABLES.keys())
        params = {
            'get': variables,
            'for': f'tract:{tract_fips}',
            'in': f'state:{state_fips}+county:{county_fips}',
            'key': self.api_key
        }

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetching ACS data for GEOID {geoid} (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()

                # Parse response
                result = self._parse_acs_response(data, geoid)

                # Cache successful results
                if result['success']:
                    self.cache[geoid] = result
                    self._save_cache()

                return result

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # Tract doesn't exist in ACS data
                    logger.warning(f"Tract {geoid} not found in ACS data")
                    result = self._create_empty_result(geoid, "Tract not found in ACS")
                    self.cache[geoid] = result
                    self._save_cache()
                    return result
                elif e.response.status_code == 429:
                    # Rate limited
                    logger.warning(f"Rate limited on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** (attempt + 1))  # Exponential backoff
                    else:
                        return self._create_empty_result(geoid, "Rate limit exceeded")
                else:
                    logger.error(f"HTTP error {e.response.status_code} for {geoid}")
                    return self._create_empty_result(geoid, f"HTTP {e.response.status_code}")

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {geoid}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return self._create_empty_result(geoid, "API timeout")

            except Exception as e:
                logger.error(f"Error fetching ACS data for {geoid}: {e}")
                return self._create_empty_result(geoid, str(e))

        return self._create_empty_result(geoid, "Max retries exceeded")

    def _parse_acs_response(self, data: List, geoid: str) -> Dict:
        """
        Parse ACS API response.

        Args:
            data: JSON response from API (list of lists)
            geoid: Census tract GEOID

        Returns:
            Parsed result dictionary
        """
        try:
            if len(data) < 2:
                return self._create_empty_result(geoid, "Empty response")

            # First row is headers, second row is data
            headers = data[0]
            values = data[1]

            # Create result dict
            result = {
                'geoid': geoid,
                'success': True,
                'error': None
            }

            # Parse each variable
            null_count = 0
            for var_code, var_name in self.ACS_VARIABLES.items():
                if var_code in headers:
                    idx = headers.index(var_code)
                    raw_value = values[idx] if idx < len(values) else None
                    clean_value = self._clean_value(raw_value)
                    result[var_name] = clean_value

                    if clean_value is None:
                        null_count += 1
                else:
                    result[var_name] = None
                    null_count += 1

            # Flag if data is incomplete
            result['data_complete'] = (null_count == 0)

            if null_count > 0:
                logger.warning(f"GEOID {geoid}: {null_count}/{len(self.ACS_VARIABLES)} variables missing")

            return result

        except Exception as e:
            logger.error(f"Error parsing ACS response for {geoid}: {e}")
            return self._create_empty_result(geoid, f"Parse error: {str(e)}")

    def _create_empty_result(self, geoid: str, error_msg: str) -> Dict:
        """Create empty result dict for failed requests."""
        result = {
            'geoid': geoid,
            'success': False,
            'error': error_msg,
            'data_complete': False
        }

        # Add all variables as None
        for var_name in self.ACS_VARIABLES.values():
            result[var_name] = None

        return result

    def batch_collect_demographics(
        self,
        tracts_df: pd.DataFrame,
        state_col: str = 'census_state_fips',
        county_col: str = 'census_county_fips',
        tract_col: str = 'census_tract_fips',
        checkpoint_file: str = "data/census/intermediate/demographics_collected.csv",
        rate_limit_delay: float = 0.5
    ) -> pd.DataFrame:
        """
        Collect demographics for all tracts in dataframe.

        Args:
            tracts_df: DataFrame with census tract identifiers
            state_col: Column name for state FIPS
            county_col: Column name for county FIPS
            tract_col: Column name for tract FIPS
            checkpoint_file: File for saving intermediate results
            rate_limit_delay: Delay between API requests (seconds)

        Returns:
            DataFrame with added ACS demographic columns
        """
        logger.info(f"Starting batch ACS data collection")

        # Create copy to avoid modifying original
        result_df = tracts_df.copy()

        # Get unique tracts to minimize API calls
        unique_tracts = result_df[
            [state_col, county_col, tract_col]
        ].drop_duplicates().dropna()

        logger.info(f"Collecting demographics for {len(unique_tracts)} unique census tracts")

        # Initialize demographics dict
        demographics_dict = {}

        # Process unique tracts
        success_count = 0
        error_count = 0
        cached_count = 0

        for idx, row in unique_tracts.iterrows():
            state_fips = row[state_col]
            county_fips = row[county_col]
            tract_fips = row[tract_col]

            geoid = f"{state_fips}{county_fips}{tract_fips}"

            # Check if already in cache (to report cache hits)
            if geoid in self.cache:
                cached_count += 1

            # Fetch demographics
            demographics = self.get_tract_demographics(
                state_fips, county_fips, tract_fips
            )

            demographics_dict[geoid] = demographics

            if demographics['success']:
                success_count += 1
            else:
                error_count += 1
                logger.warning(f"Failed to fetch demographics for {geoid}: {demographics['error']}")

            # Progress logging
            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(unique_tracts)} unique tracts "
                           f"({success_count} success, {error_count} errors, {cached_count} cached)")

            # Rate limiting (unless cached)
            if geoid not in self.cache:
                time.sleep(rate_limit_delay)

        # Join demographics back to original dataframe
        logger.info("Merging demographics into dispensary dataset")

        # Create GEOID column for merging
        result_df['_temp_geoid'] = (
            result_df[state_col].astype(str) +
            result_df[county_col].astype(str) +
            result_df[tract_col].astype(str)
        )

        # Add demographic columns
        for var_name in self.ACS_VARIABLES.values():
            result_df[var_name] = None

        result_df['census_data_complete'] = False
        result_df['census_api_error'] = False

        # Map demographics
        for idx, row in result_df.iterrows():
            geoid = row['_temp_geoid']

            if pd.isna(geoid) or geoid == 'nannannan':
                result_df.at[idx, 'census_api_error'] = True
                continue

            if geoid in demographics_dict:
                demo = demographics_dict[geoid]

                # Set variables
                for var_name in self.ACS_VARIABLES.values():
                    result_df.at[idx, var_name] = demo.get(var_name)

                result_df.at[idx, 'census_data_complete'] = demo.get('data_complete', False)
                result_df.at[idx, 'census_api_error'] = not demo.get('success', False)

        # Remove temporary column
        result_df = result_df.drop(columns=['_temp_geoid'])

        # Save checkpoint
        logger.info(f"Saving checkpoint to {checkpoint_file}")
        checkpoint_path = Path(checkpoint_file)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(checkpoint_file, index=False)

        # Summary
        complete_count = result_df['census_data_complete'].sum()
        logger.info(f"ACS data collection complete:")
        logger.info(f"  Unique tracts: {len(unique_tracts)}")
        logger.info(f"  Success: {success_count} ({success_count/len(unique_tracts)*100:.1f}%)")
        logger.info(f"  Errors: {error_count}")
        logger.info(f"  Cached: {cached_count}")
        logger.info(f"  Complete data: {complete_count}/{len(result_df)} dispensaries")

        return result_df


# Module test
if __name__ == "__main__":
    # Test with sample tracts
    collector = ACSDataCollector()

    # Miami test (GEOID: 12086006713)
    miami_demo = collector.get_tract_demographics('12', '086', '006713')
    print("\nMiami tract demographics:")
    for key, value in miami_demo.items():
        print(f"  {key}: {value}")

    # Philadelphia test (GEOID: 42101000500)
    philly_demo = collector.get_tract_demographics('42', '101', '000500')
    print("\nPhiladelphia tract demographics:")
    for key, value in philly_demo.items():
        print(f"  {key}: {value}")
