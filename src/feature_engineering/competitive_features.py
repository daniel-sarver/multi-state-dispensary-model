"""
Competitive Feature Engineering Module

Calculates competitive metrics for dispensaries including:
- Multi-radius competitor counts (1, 3, 5, 10, 20 miles)
- Distance-weighted competition scores
- Market saturation metrics (dispensaries per capita)
- Demographic interaction features

Part of Phase 3: Model Development
Multi-State Dispensary Prediction Model
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from geopy.distance import geodesic

logger = logging.getLogger(__name__)


class CompetitiveFeatureEngineer:
    """
    Engineer competitive features for dispensary prediction model.

    Features created:
    1. Multi-radius competitor counts (1, 3, 5, 10, 20 miles)
    2. Distance-weighted competition scores
    3. Market saturation (competitors per 100k population)
    4. Demographic interactions (affluent market size, educated urban markets, etc.)
    """

    # Competition analysis radii (miles)
    RADII = [1, 3, 5, 10, 20]

    def __init__(self):
        """Initialize the CompetitiveFeatureEngineer."""
        logger.info("CompetitiveFeatureEngineer initialized")

    def calculate_distance_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """
        Calculate distance matrix between all dispensaries.

        Args:
            df: DataFrame with latitude/longitude columns

        Returns:
            NxN matrix of distances in miles
        """
        n = len(df)
        distances = np.zeros((n, n))

        coords = df[['latitude', 'longitude']].values

        logger.info(f"Calculating distance matrix for {n} dispensaries")

        for i in range(n):
            if i > 0 and i % 100 == 0:
                logger.info(f"  Processed {i}/{n} dispensaries")

            for j in range(i + 1, n):
                # Calculate geodesic distance in miles
                dist = geodesic(coords[i], coords[j]).miles
                distances[i, j] = dist
                distances[j, i] = dist

        logger.info(f"Distance matrix calculation complete: {n}x{n}")
        return distances

    def calculate_competitor_counts(
        self,
        df: pd.DataFrame,
        distances: np.ndarray
    ) -> pd.DataFrame:
        """
        Calculate competitor counts at multiple radii.

        Args:
            df: DataFrame with dispensary data
            distances: Distance matrix (miles)

        Returns:
            DataFrame with competitor count columns added
        """
        df = df.copy()

        logger.info("Calculating multi-radius competitor counts")

        for radius in self.RADII:
            col_name = f'competitors_{radius}mi'

            # Count competitors within radius (excluding self)
            # Each row counts dispensaries within radius of that dispensary
            counts = (distances < radius).sum(axis=1) - 1  # -1 to exclude self

            df[col_name] = counts

            logger.info(f"  {col_name}: mean={counts.mean():.1f}, max={counts.max()}")

        return df

    def calculate_distance_weighted_competition(
        self,
        df: pd.DataFrame,
        distances: np.ndarray
    ) -> pd.DataFrame:
        """
        Calculate distance-weighted competition scores.

        Competition score = Σ(1 / distance) for all competitors within 20 miles
        Closer competitors have higher weight.

        Args:
            df: DataFrame with dispensary data
            distances: Distance matrix (miles)

        Returns:
            DataFrame with weighted competition column added
        """
        df = df.copy()

        logger.info("Calculating distance-weighted competition scores")

        # Create weight matrix: 1/distance for distances < 20 miles, 0 otherwise
        # Avoid division by zero (self) by setting diagonal to 0
        with np.errstate(divide='ignore', invalid='ignore'):
            weights = np.where(
                (distances < 20) & (distances > 0),
                1.0 / distances,
                0
            )

        # Sum weights for each dispensary
        competition_scores = weights.sum(axis=1)

        df['competition_weighted_20mi'] = competition_scores

        logger.info(f"  Weighted competition: mean={competition_scores.mean():.2f}, "
                   f"max={competition_scores.max():.2f}")

        return df

    def calculate_market_saturation(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate market saturation metrics.

        Saturation = competitors per 100k population at various radii

        Args:
            df: DataFrame with competitor counts and population columns

        Returns:
            DataFrame with saturation columns added
        """
        df = df.copy()

        logger.info("Calculating market saturation metrics")

        for radius in self.RADII:
            pop_col = f'pop_{radius}mi'
            comp_col = f'competitors_{radius}mi'
            sat_col = f'saturation_{radius}mi'

            if pop_col in df.columns:
                # Saturation = (competitors / population) * 100,000
                # Handle division by zero
                df[sat_col] = np.where(
                    df[pop_col] > 0,
                    (df[comp_col] / df[pop_col]) * 100000,
                    0
                )

                logger.info(f"  {sat_col}: mean={df[sat_col].mean():.2f} per 100k")
            else:
                logger.warning(f"  Skipping {sat_col} - {pop_col} not found")

        return df

    def calculate_demographic_interactions(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate demographic interaction features.

        Creates:
        1. Affluent market size: pop_5mi × median_household_income
        2. Educated urban markets: pct_bachelor_plus × population_density
        3. Age-adjusted catchment: median_age × pop_3mi

        Args:
            df: DataFrame with demographic columns

        Returns:
            DataFrame with interaction columns added
        """
        df = df.copy()

        logger.info("Calculating demographic interaction features")

        # 1. Affluent market size
        if 'pop_5mi' in df.columns and 'median_household_income' in df.columns:
            df['affluent_market_5mi'] = df['pop_5mi'] * df['median_household_income'] / 1e6
            logger.info(f"  affluent_market_5mi: mean={df['affluent_market_5mi'].mean():.1f}M")
        else:
            logger.warning("  Skipping affluent_market_5mi - required columns missing")

        # 2. Educated urban markets
        if 'pct_bachelor_plus' in df.columns and 'population_density' in df.columns:
            df['educated_urban_score'] = df['pct_bachelor_plus'] * df['population_density']
            logger.info(f"  educated_urban_score: mean={df['educated_urban_score'].mean():.1f}")
        else:
            logger.warning("  Skipping educated_urban_score - required columns missing")

        # 3. Age-adjusted catchment
        if 'median_age' in df.columns and 'pop_3mi' in df.columns:
            df['age_adjusted_catchment_3mi'] = df['median_age'] * df['pop_3mi'] / 1000
            logger.info(f"  age_adjusted_catchment_3mi: mean={df['age_adjusted_catchment_3mi'].mean():.1f}k")
        else:
            logger.warning("  Skipping age_adjusted_catchment_3mi - required columns missing")

        return df

    def engineer_features(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Main method to engineer all competitive features.

        Note: Competition metrics are calculated for ALL dispensaries with valid
        coordinates (training + regulator-only), because competitive pressure
        comes from the entire market, not just training dispensaries.

        Args:
            df: DataFrame with dispensary data (must have latitude, longitude)

        Returns:
            DataFrame with all competitive features added
        """
        logger.info("================================================================================")
        logger.info("COMPETITIVE FEATURE ENGINEERING")
        logger.info("================================================================================")

        # Validate required columns
        required = ['latitude', 'longitude']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        logger.info(f"Input dataset: {len(df)} dispensaries")

        # Filter to valid coordinates only
        valid_mask = df['latitude'].notna() & df['longitude'].notna()
        logger.info(f"Valid coordinates: {valid_mask.sum()}/{len(df)}")

        # Calculate distance matrix for all dispensaries
        # This is needed even if we only engineer features for training data,
        # because competition comes from ALL dispensaries (training + regulator-only)
        distances = self.calculate_distance_matrix(df[valid_mask])

        # Create copy for feature engineering
        df_valid = df[valid_mask].copy().reset_index(drop=True)

        # Calculate all competitive features
        df_valid = self.calculate_competitor_counts(df_valid, distances)
        df_valid = self.calculate_distance_weighted_competition(df_valid, distances)
        df_valid = self.calculate_market_saturation(df_valid)
        df_valid = self.calculate_demographic_interactions(df_valid)

        # Merge back with original dataframe
        # Get list of new columns
        new_cols = [col for col in df_valid.columns if col not in df.columns]

        logger.info(f"\nCreated {len(new_cols)} new competitive features:")
        for col in sorted(new_cols):
            logger.info(f"  - {col}")

        # Merge engineered features back
        df_result = df.copy()
        for col in new_cols:
            df_result[col] = np.nan

        # Update valid rows
        df_result.loc[valid_mask, new_cols] = df_valid[new_cols].values

        # Summary statistics
        logger.info("\n" + "="*80)
        logger.info("FEATURE ENGINEERING COMPLETE")
        logger.info("="*80)
        logger.info(f"Total dispensaries: {len(df_result)}")
        logger.info(f"With competitive features: {valid_mask.sum()}")
        logger.info(f"New columns added: {len(new_cols)}")

        return df_result


def main():
    """Example usage and testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load test data
    logger.info("Loading datasets for testing...")
    fl_df = pd.read_csv('data/processed/FL_combined_dataset_current.csv')
    pa_df = pd.read_csv('data/processed/PA_combined_dataset_current.csv')

    # Combine for multi-state analysis
    combined_df = pd.concat([fl_df, pa_df], ignore_index=True)

    logger.info(f"Combined dataset: {len(combined_df)} dispensaries")
    logger.info(f"  FL: {len(fl_df)}")
    logger.info(f"  PA: {len(pa_df)}")

    # Engineer features
    engineer = CompetitiveFeatureEngineer()
    result_df = engineer.engineer_features(combined_df)

    # Save results
    output_path = 'data/processed/combined_with_competitive_features.csv'
    result_df.to_csv(output_path, index=False)
    logger.info(f"\nSaved results to {output_path}")

    # Display sample
    logger.info("\nSample competitive features:")
    comp_cols = [col for col in result_df.columns if 'competitor' in col or 'saturation' in col]
    print(result_df[['state', 'regulator_name'] + comp_cols].head(10))


if __name__ == '__main__':
    main()
