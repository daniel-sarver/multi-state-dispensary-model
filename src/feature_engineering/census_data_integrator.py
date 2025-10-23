"""
Census Data Integrator Module

Merges census demographic features with combined dispensary datasets.

Features:
- Preserves all original columns
- Adds data quality flags
- Generates comprehensive validation report
- Updates combined datasets with census features

Author: Multi-State Dispensary Model - Phase 2
Date: October 2025
"""

import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CensusDataIntegrator:
    """
    Integrates census features into combined dispensary datasets.

    Features:
    - Preserves original data integrity
    - Adds census features as new columns
    - Comprehensive data quality validation
    - Detailed reporting and statistics
    """

    # Census feature columns to add
    CENSUS_TRACT_COLS = [
        'census_state_fips',
        'census_county_fips',
        'census_tract_fips',
        'census_geoid',
        'census_tract_name'
    ]

    ACS_DEMOGRAPHIC_COLS = [
        'total_population',
        'median_age',
        'median_household_income',
        'per_capita_income',
        'total_pop_25_plus',
        'bachelors_degree',
        'masters_degree',
        'professional_degree',
        'doctorate_degree'
    ]

    MULTI_RADIUS_COLS = [
        'pop_1mi',
        'pop_3mi',
        'pop_5mi',
        'pop_10mi',
        'pop_20mi'
    ]

    DERIVED_FEATURE_COLS = [
        'pct_bachelor_plus',
        'population_density'
    ]

    DATA_QUALITY_COLS = [
        'census_tract_error',
        'census_data_complete',
        'census_api_error',
        'census_collection_date'
    ]

    def __init__(self):
        """Initialize Census Data Integrator."""
        logger.info("CensusDataIntegrator initialized")

    def integrate_census_data(
        self,
        combined_df: pd.DataFrame,
        census_df: pd.DataFrame,
        join_key: str = 'Dispensary_ID'
    ) -> pd.DataFrame:
        """
        Merge census features into combined dataset.

        Args:
            combined_df: Original combined dataset (FL or PA)
            census_df: DataFrame with census features
            join_key: Column to join on (default: Dispensary_ID)

        Returns:
            DataFrame with integrated census features
        """
        logger.info(f"Integrating census data into combined dataset")
        logger.info(f"  Original rows: {len(combined_df)}")
        logger.info(f"  Census rows: {len(census_df)}")

        # Verify join key exists
        if join_key not in combined_df.columns:
            logger.error(f"Join key '{join_key}' not found in combined dataset")
            raise ValueError(f"Missing join key: {join_key}")

        if join_key not in census_df.columns:
            logger.error(f"Join key '{join_key}' not found in census dataset")
            raise ValueError(f"Missing join key: {join_key}")

        # Get census columns to add
        census_cols_to_add = []
        for col_list in [
            self.CENSUS_TRACT_COLS,
            self.ACS_DEMOGRAPHIC_COLS,
            self.MULTI_RADIUS_COLS,
            self.DERIVED_FEATURE_COLS,
            self.DATA_QUALITY_COLS
        ]:
            for col in col_list:
                if col in census_df.columns:
                    census_cols_to_add.append(col)

        logger.info(f"  Adding {len(census_cols_to_add)} census columns")

        # Merge
        result_df = combined_df.merge(
            census_df[[join_key] + census_cols_to_add],
            on=join_key,
            how='left'
        )

        # Add collection timestamp
        result_df['census_collection_date'] = datetime.now().strftime('%Y-%m-%d')

        # Log merge results
        logger.info(f"  Result rows: {len(result_df)}")
        logger.info(f"  Census features added successfully")

        return result_df

    def validate_integration(self, df: pd.DataFrame) -> Dict:
        """
        Validate census data quality and generate report.

        Args:
            df: DataFrame with integrated census data

        Returns:
            dict: {
                'total_dispensaries': int,
                'census_complete': int,
                'census_partial': int,
                'census_missing': int,
                'pct_complete': float,
                'null_counts': dict,
                'value_ranges': dict,
                'population_monotonic': dict
            }
        """
        logger.info("Validating census data integration")

        validation = {
            'total_dispensaries': len(df),
            'null_counts': {},
            'value_ranges': {},
            'population_monotonic': {}
        }

        # Count completion levels
        has_geoid = df['census_geoid'].notna()
        has_demographics = df['total_population'].notna()
        has_multi_radius = df['pop_1mi'].notna()

        validation['census_complete'] = (has_geoid & has_demographics & has_multi_radius).sum()
        validation['census_partial'] = (has_geoid & (has_demographics | has_multi_radius)).sum()
        validation['census_missing'] = (~has_geoid).sum()

        validation['pct_complete'] = (
            validation['census_complete'] / validation['total_dispensaries'] * 100
        )

        # Null counts for each column
        for col_list in [
            self.CENSUS_TRACT_COLS,
            self.ACS_DEMOGRAPHIC_COLS,
            self.MULTI_RADIUS_COLS,
            self.DERIVED_FEATURE_COLS
        ]:
            for col in col_list:
                if col in df.columns:
                    null_count = df[col].isna().sum()
                    null_pct = (null_count / len(df)) * 100
                    validation['null_counts'][col] = {
                        'count': int(null_count),
                        'percent': round(null_pct, 1)
                    }

        # Value ranges for numeric columns
        numeric_cols = [
            'total_population',
            'median_age',
            'median_household_income',
            'per_capita_income',
            'pct_bachelor_plus',
            'population_density',
            'pop_1mi',
            'pop_3mi',
            'pop_5mi',
            'pop_10mi',
            'pop_20mi'
        ]

        for col in numeric_cols:
            if col in df.columns and df[col].notna().sum() > 0:
                validation['value_ranges'][col] = {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median())
                }

        # Validate monotonic increase for multi-radius populations
        if all(f'pop_{r}mi' in df.columns for r in [1, 3, 5, 10, 20]):
            monotonic_count = 0
            non_monotonic_indices = []

            for idx, row in df.iterrows():
                pops = [row[f'pop_{r}mi'] for r in [1, 3, 5, 10, 20]]

                # Skip if any are missing
                if any(pd.isna(p) for p in pops):
                    continue

                # Check monotonic
                is_monotonic = all(pops[i] <= pops[i+1] for i in range(len(pops)-1))

                if is_monotonic:
                    monotonic_count += 1
                else:
                    non_monotonic_indices.append(idx)

            total_with_data = df['pop_1mi'].notna().sum()
            validation['population_monotonic'] = {
                'total_with_data': int(total_with_data),
                'monotonic': int(monotonic_count),
                'non_monotonic': int(len(non_monotonic_indices)),
                'pct_monotonic': round((monotonic_count / total_with_data * 100), 1) if total_with_data > 0 else 0,
                'non_monotonic_indices': non_monotonic_indices[:10]  # First 10 for debugging
            }

        logger.info(f"Validation complete:")
        logger.info(f"  Total: {validation['total_dispensaries']}")
        logger.info(f"  Complete: {validation['census_complete']} ({validation['pct_complete']:.1f}%)")
        logger.info(f"  Partial: {validation['census_partial']}")
        logger.info(f"  Missing: {validation['census_missing']}")

        return validation

    def generate_summary_report(
        self,
        validation_results: Dict,
        output_file: str = "data/census/census_integration_report.json"
    ) -> None:
        """
        Create JSON summary of census integration quality.

        Args:
            validation_results: Results from validate_integration()
            output_file: Path to save report
        """
        logger.info(f"Generating summary report: {output_file}")

        # Add metadata
        report = {
            'generated_at': datetime.now().isoformat(),
            'phase': 'Phase 2 - Census Demographics Integration',
            'validation': validation_results
        }

        # Save as JSON
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to {output_file}")

    def save_updated_dataset(
        self,
        df: pd.DataFrame,
        output_file: str,
        archive_original: bool = True
    ) -> None:
        """
        Save updated dataset with census features.

        Args:
            df: DataFrame with integrated census data
            output_file: Path to save updated dataset
            archive_original: Whether to archive the original file
        """
        output_path = Path(output_file)

        # Archive original if it exists
        if archive_original and output_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_file = output_path.parent / f"{output_path.stem}_pre_census_{timestamp}.csv"
            logger.info(f"Archiving original to {archive_file}")
            output_path.rename(archive_file)

        # Save updated dataset
        logger.info(f"Saving updated dataset to {output_file}")
        df.to_csv(output_file, index=False)
        logger.info(f"Saved {len(df)} rows with {len(df.columns)} columns")


# Module test
if __name__ == "__main__":
    # Test with sample data
    integrator = CensusDataIntegrator()

    # Create sample combined dataset
    combined_sample = pd.DataFrame({
        'Dispensary_ID': ['FL_001', 'FL_002', 'PA_001'],
        'Dispensary_Name': ['Miami Dispensary', 'Tampa Dispensary', 'Philly Dispensary'],
        'latitude': [25.761681, 27.950575, 39.952583],
        'longitude': [-80.191788, -82.457177, -75.165222],
        'total_visits_week': [1000, 1200, 900]
    })

    # Create sample census dataset
    census_sample = pd.DataFrame({
        'Dispensary_ID': ['FL_001', 'FL_002', 'PA_001'],
        'census_geoid': ['12086006713', '12057990101', '42101000500'],
        'total_population': [1912, 2500, 3292],
        'median_household_income': [135809, 85000, 68977],
        'pct_bachelor_plus': [85.2, 45.3, 50.0],
        'pop_1mi': [15000, 8000, 25000],
        'pop_3mi': [45000, 30000, 75000],
        'pop_5mi': [120000, 80000, 180000],
        'pop_10mi': [350000, 250000, 500000],
        'pop_20mi': [1200000, 800000, 1500000],
        'census_data_complete': [True, True, True],
        'census_tract_error': [False, False, False]
    })

    # Integrate
    integrated = integrator.integrate_census_data(combined_sample, census_sample)

    print("\nIntegrated dataset sample:")
    print(integrated[['Dispensary_Name', 'total_population', 'pop_1mi', 'pop_5mi', 'pop_20mi']].head())

    # Validate
    validation = integrator.validate_integration(integrated)

    print("\nValidation summary:")
    print(f"  Total: {validation['total_dispensaries']}")
    print(f"  Complete: {validation['census_complete']} ({validation['pct_complete']:.1f}%)")
    print(f"  Monotonic populations: {validation['population_monotonic']}")
