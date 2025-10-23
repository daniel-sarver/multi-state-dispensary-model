"""
Census Feature Engineer Module

Calculates derived demographic features from raw census variables.

Features:
- Education percentage (bachelor's degree or higher)
- Population density (people per square mile)
- Value validation and range checking

Author: Multi-State Dispensary Model - Phase 2
Date: October 2025
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CensusFeatureEngineer:
    """
    Engineers derived features from raw census variables.

    Calculations:
    - pct_bachelor_plus: % population 25+ with bachelor's degree or higher
    - population_density: People per square mile (using tract area)

    Features:
    - Null value handling
    - Value range validation
    - Anomaly flagging
    """

    def __init__(self):
        """Initialize Census Feature Engineer."""
        logger.info("CensusFeatureEngineer initialized")

    def calculate_education_percentage(
        self,
        bachelors: float,
        masters: float,
        professional: float,
        doctorate: float,
        total_25_plus: float
    ) -> Optional[float]:
        """
        Calculate % population 25+ with bachelor's degree or higher.

        Args:
            bachelors: Number with bachelor's degree (B15003_022E)
            masters: Number with master's degree (B15003_023E)
            professional: Number with professional degree (B15003_024E)
            doctorate: Number with doctorate (B15003_025E)
            total_25_plus: Total population 25+ (B15003_001E)

        Returns:
            Percentage with bachelor's+ or None if data missing
        """
        # Check for missing values
        if pd.isna(total_25_plus) or total_25_plus == 0:
            return None

        # Sum education levels (treat NaN as 0)
        bachelors_plus = sum([
            bachelors if not pd.isna(bachelors) else 0,
            masters if not pd.isna(masters) else 0,
            professional if not pd.isna(professional) else 0,
            doctorate if not pd.isna(doctorate) else 0
        ])

        # Calculate percentage
        percentage = (bachelors_plus / total_25_plus) * 100

        # Validate range (0-100%)
        if percentage < 0 or percentage > 100:
            logger.warning(f"Invalid education percentage: {percentage:.1f}%")
            return None

        return percentage

    def calculate_population_density(
        self,
        population: float,
        tract_area_sqm: float
    ) -> Optional[float]:
        """
        Calculate population per square mile.

        Args:
            population: Total population (B01001_001E)
            tract_area_sqm: Tract area in square meters

        Returns:
            People per square mile or None if data missing
        """
        # Check for missing values
        if pd.isna(population) or pd.isna(tract_area_sqm) or tract_area_sqm == 0:
            return None

        # Convert square meters to square miles
        # 1 square mile = 2,589,988 square meters
        SQM_PER_SQ_MILE = 2589988
        tract_area_sq_miles = tract_area_sqm / SQM_PER_SQ_MILE

        # Calculate density
        density = population / tract_area_sq_miles

        # Validate range (0-100,000 per sq mi reasonable max)
        if density < 0 or density > 100000:
            logger.warning(f"Unusual population density: {density:.1f} per sq mi")
            # Don't reject, just warn
            pass

        return density

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all derived census features to dataframe.

        Adds columns:
        - pct_bachelor_plus: % with bachelor's degree or higher
        - population_density: People per square mile

        Args:
            df: DataFrame with raw census variables

        Returns:
            DataFrame with added derived features
        """
        logger.info(f"Engineering census features for {len(df)} dispensaries")

        # Create copy
        result_df = df.copy()

        # Initialize derived feature columns
        result_df['pct_bachelor_plus'] = None
        result_df['population_density'] = None

        # Calculate education percentage
        logger.info("Calculating education percentages")
        for idx, row in result_df.iterrows():
            result_df.at[idx, 'pct_bachelor_plus'] = self.calculate_education_percentage(
                row.get('bachelors_degree'),
                row.get('masters_degree'),
                row.get('professional_degree'),
                row.get('doctorate_degree'),
                row.get('total_pop_25_plus')
            )

        # Calculate population density
        logger.info("Calculating population density")
        for idx, row in result_df.iterrows():
            # Need tract area - try to get from tract_area_sqm column
            # If not available, skip density calculation
            tract_area = row.get('tract_area_sqm')

            if pd.notna(tract_area):
                result_df.at[idx, 'population_density'] = self.calculate_population_density(
                    row.get('total_population'),
                    tract_area
                )

        # Summary statistics
        pct_complete_edu = result_df['pct_bachelor_plus'].notna().sum()
        pct_complete_density = result_df['population_density'].notna().sum()

        logger.info(f"Feature engineering complete:")
        logger.info(f"  Education %: {pct_complete_edu}/{len(df)} ({pct_complete_edu/len(df)*100:.1f}%)")
        logger.info(f"  Density: {pct_complete_density}/{len(df)} ({pct_complete_density/len(df)*100:.1f}%)")

        # Log summary statistics
        if pct_complete_edu > 0:
            logger.info(f"  Education % range: {result_df['pct_bachelor_plus'].min():.1f}% - "
                       f"{result_df['pct_bachelor_plus'].max():.1f}%")
            logger.info(f"  Education % mean: {result_df['pct_bachelor_plus'].mean():.1f}%")

        if pct_complete_density > 0:
            logger.info(f"  Density range: {result_df['population_density'].min():.0f} - "
                       f"{result_df['population_density'].max():.0f} per sq mi")
            logger.info(f"  Density mean: {result_df['population_density'].mean():.0f} per sq mi")

        return result_df

    def validate_features(self, df: pd.DataFrame) -> Dict:
        """
        Validate derived feature quality.

        Args:
            df: DataFrame with derived features

        Returns:
            dict: {
                'education_pct_complete': int,
                'education_pct_mean': float,
                'density_complete': int,
                'density_mean': float,
                'anomalies': list[dict]
            }
        """
        validation = {
            'education_pct_complete': df['pct_bachelor_plus'].notna().sum(),
            'education_pct_mean': df['pct_bachelor_plus'].mean(),
            'density_complete': df['population_density'].notna().sum(),
            'density_mean': df['population_density'].mean(),
            'anomalies': []
        }

        # Check for anomalies
        for idx, row in df.iterrows():
            # Very high education percentage (>70% unusual)
            if pd.notna(row.get('pct_bachelor_plus')) and row['pct_bachelor_plus'] > 70:
                validation['anomalies'].append({
                    'index': idx,
                    'type': 'high_education',
                    'value': row['pct_bachelor_plus']
                })

            # Very high density (>50,000 per sq mi is very urban)
            if pd.notna(row.get('population_density')) and row['population_density'] > 50000:
                validation['anomalies'].append({
                    'index': idx,
                    'type': 'high_density',
                    'value': row['population_density']
                })

            # Very low income (< $20k unusual)
            if pd.notna(row.get('median_household_income')) and row['median_household_income'] < 20000:
                validation['anomalies'].append({
                    'index': idx,
                    'type': 'low_income',
                    'value': row['median_household_income']
                })

        return validation


# Module test
if __name__ == "__main__":
    # Test with sample data
    engineer = CensusFeatureEngineer()

    # Create sample dataframe
    sample_df = pd.DataFrame({
        'total_pop_25_plus': [1592, 2910],
        'bachelors_degree': [623, 727],
        'masters_degree': [575, 317],
        'professional_degree': [126, 330],
        'doctorate_degree': [33, 81],
        'total_population': [1912, 3292],
        'tract_area_sqm': [2000000, 5000000]  # ~0.77 sq mi, ~1.93 sq mi
    })

    # Calculate education percentages
    sample_df['pct_bachelor_plus'] = sample_df.apply(
        lambda row: engineer.calculate_education_percentage(
            row['bachelors_degree'],
            row['masters_degree'],
            row['professional_degree'],
            row['doctorate_degree'],
            row['total_pop_25_plus']
        ),
        axis=1
    )

    # Calculate densities
    sample_df['population_density'] = sample_df.apply(
        lambda row: engineer.calculate_population_density(
            row['total_population'],
            row['tract_area_sqm']
        ),
        axis=1
    )

    print("\nSample feature engineering results:")
    print(sample_df[['pct_bachelor_plus', 'population_density']])

    # Test validation
    validation = engineer.validate_features(sample_df)
    print("\nValidation results:")
    for key, value in validation.items():
        if key != 'anomalies':
            print(f"  {key}: {value}")
