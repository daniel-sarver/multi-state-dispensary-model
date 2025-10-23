"""
Census Data Collection Orchestration Script

Main script that orchestrates the entire census data collection pipeline:
1. Census tract identification
2. ACS demographics collection
3. Multi-radius population analysis with area-weighting
4. Feature engineering
5. Data integration with combined datasets

Author: Multi-State Dispensary Model - Phase 2
Date: October 2025
"""

import pandas as pd
import geopandas as gpd
import sys
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import census modules
from src.feature_engineering.census_tract_identifier import CensusTractIdentifier
from src.feature_engineering.acs_data_collector import ACSDataCollector
from src.feature_engineering.geographic_analyzer import GeographicAnalyzer
from src.feature_engineering.census_feature_engineer import CensusFeatureEngineer
from src.feature_engineering.census_data_integrator import CensusDataIntegrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'census_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


def load_combined_datasets(
    fl_file: str = "data/processed/FL_combined_dataset_current.csv",
    pa_file: str = "data/processed/PA_combined_dataset_current.csv",
    training_only: bool = True
) -> pd.DataFrame:
    """
    Load combined datasets for FL and PA.

    Args:
        fl_file: Path to FL combined dataset
        pa_file: Path to PA combined dataset
        training_only: If True, filter to has_placer_data only

    Returns:
        Combined DataFrame with state_abbr column and dispensary_id
    """
    logger.info("=" * 80)
    logger.info("STEP 0: Loading combined datasets")
    logger.info("=" * 80)

    # Load datasets
    logger.info(f"Loading FL data from {fl_file}")
    fl_df = pd.read_csv(fl_file)
    fl_df['state_abbr'] = 'FL'
    # Create unique ID using state + row index from original file
    fl_df['dispensary_id'] = ['FL_' + str(i).zfill(4) for i in range(len(fl_df))]

    logger.info(f"Loading PA data from {pa_file}")
    pa_df = pd.read_csv(pa_file)
    pa_df['state_abbr'] = 'PA'
    # Create unique ID using state + row index from original file
    pa_df['dispensary_id'] = ['PA_' + str(i).zfill(4) for i in range(len(pa_df))]

    # Combine
    combined_df = pd.concat([fl_df, pa_df], ignore_index=True)

    logger.info(f"Loaded {len(fl_df)} FL + {len(pa_df)} PA = {len(combined_df)} total dispensaries")

    # Filter to training dispensaries if requested
    if training_only and 'has_placer_data' in combined_df.columns:
        combined_df = combined_df[combined_df['has_placer_data'] == True].copy()
        logger.info(f"Filtered to {len(combined_df)} training dispensaries (has_placer_data = True)")

    return combined_df


def main():
    """Main orchestration function."""
    parser = argparse.ArgumentParser(
        description='Collect census demographics for dispensaries'
    )
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Run on sample (10 FL + 10 PA) instead of full dataset'
    )
    parser.add_argument(
        '--skip-geocoding',
        action='store_true',
        help='Skip geocoding step (use existing checkpoint)'
    )
    parser.add_argument(
        '--skip-demographics',
        action='store_true',
        help='Skip ACS demographics collection (use existing checkpoint)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("CENSUS DATA COLLECTION PIPELINE")
    logger.info("Phase 2: Census Demographics Integration")
    logger.info("=" * 80)

    try:
        # Step 0: Load combined datasets
        dispensaries_df = load_combined_datasets(
            training_only=True
        )

        # Sample mode for testing
        if args.sample:
            logger.info("\n*** SAMPLE MODE: Processing 10 FL + 10 PA dispensaries ***\n")
            fl_sample = dispensaries_df[dispensaries_df['state_abbr'] == 'FL'].head(10)
            pa_sample = dispensaries_df[dispensaries_df['state_abbr'] == 'PA'].head(10)
            dispensaries_df = pd.concat([fl_sample, pa_sample], ignore_index=True)
            logger.info(f"Sample size: {len(dispensaries_df)} dispensaries")

        # Step 1: Identify census tracts
        if not args.skip_geocoding:
            logger.info("\n" + "=" * 80)
            logger.info("STEP 1: Census Tract Identification")
            logger.info("=" * 80)

            identifier = CensusTractIdentifier()
            dispensaries_df = identifier.batch_identify_tracts(
                dispensaries_df,
                lat_col='latitude',
                lon_col='longitude',
                checkpoint_file="data/census/intermediate/tracts_identified.csv"
            )
        else:
            logger.info("\nSkipping geocoding (loading checkpoint)")
            dispensaries_df = pd.read_csv("data/census/intermediate/tracts_identified.csv")

        # Step 2: Collect ACS demographics
        if not args.skip_demographics:
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: ACS Demographics Collection")
            logger.info("=" * 80)

            collector = ACSDataCollector()
            dispensaries_df = collector.batch_collect_demographics(
                dispensaries_df,
                checkpoint_file="data/census/intermediate/demographics_collected.csv"
            )
        else:
            logger.info("\nSkipping ACS collection (loading checkpoint)")
            dispensaries_df = pd.read_csv("data/census/intermediate/demographics_collected.csv")

        # Step 3: Identify all tracts intersecting buffers
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Identify All Intersecting Tracts (for Multi-Radius Analysis)")
        logger.info("=" * 80)

        analyzer = GeographicAnalyzer()

        # Collect ALL unique tract GEOIDs that intersect any buffer
        logger.info("Finding all tracts that intersect any dispensary's 20-mile buffer...")
        all_intersecting_tracts = set()

        for idx, row in dispensaries_df.iterrows():
            lat = row.get('latitude')
            lon = row.get('longitude')
            state = row.get('state_abbr')

            if pd.isna(lat) or pd.isna(lon) or pd.isna(state):
                continue

            try:
                # Create 20-mile buffer (largest radius)
                buffer, crs = analyzer.create_buffer(lat, lon, 20, state)

                # Get tracts for this state
                tracts_gdf = analyzer._get_tracts_for_state(state)

                # Find intersecting tracts
                buffer_gdf = gpd.GeoDataFrame({'geometry': [buffer]}, crs=tracts_gdf.crs)
                intersecting = gpd.sjoin(tracts_gdf, buffer_gdf, how='inner', predicate='intersects')

                # Add GEOIDs to set
                for geoid in intersecting['GEOID'].astype(str):
                    all_intersecting_tracts.add(geoid)

                if (idx + 1) % 25 == 0:
                    logger.info(f"  Processed {idx + 1}/{len(dispensaries_df)} dispensaries, "
                               f"found {len(all_intersecting_tracts)} unique tracts so far")

            except Exception as e:
                logger.error(f"Error finding tracts for row {idx}: {e}")
                continue

        logger.info(f"\nTotal unique tracts intersecting all buffers: {len(all_intersecting_tracts)}")

        # Step 4: Collect ACS demographics for ALL intersecting tracts + tract areas
        logger.info("\n" + "=" * 80)
        logger.info("STEP 4: ACS Demographics Collection (ALL Intersecting Tracts)")
        logger.info("=" * 80)

        # Create dataframe of all tracts to query, including tract areas
        logger.info("Extracting tract areas from shapefiles...")
        all_tracts_to_query = []

        # Get tract areas from loaded shapefiles
        fl_tracts = analyzer._get_tracts_for_state('FL') if 'FL' in dispensaries_df['state_abbr'].values else None
        pa_tracts = analyzer._get_tracts_for_state('PA') if 'PA' in dispensaries_df['state_abbr'].values else None

        # Create lookup dict for tract areas
        tract_area_lookup = {}
        if fl_tracts is not None:
            for _, tract in fl_tracts.iterrows():
                geoid = str(tract['GEOID'])
                tract_area_lookup[geoid] = tract['tract_area_sqm']

        if pa_tracts is not None:
            for _, tract in pa_tracts.iterrows():
                geoid = str(tract['GEOID'])
                tract_area_lookup[geoid] = tract['tract_area_sqm']

        logger.info(f"Extracted {len(tract_area_lookup)} tract areas")

        # Create dataframe with GEOIDs and areas
        for geoid in all_intersecting_tracts:
            if len(geoid) == 11:  # Valid GEOID
                all_tracts_to_query.append({
                    'census_geoid': geoid,
                    'census_state_fips': geoid[:2],
                    'census_county_fips': geoid[2:5],
                    'census_tract_fips': geoid[5:11],
                    'tract_area_sqm': tract_area_lookup.get(geoid)
                })

        all_tracts_df = pd.DataFrame(all_tracts_to_query)
        logger.info(f"Querying ACS demographics for {len(all_tracts_df)} tracts...")

        # Use existing collector
        all_tracts_with_demographics = collector.batch_collect_demographics(
            all_tracts_df,
            checkpoint_file="data/census/intermediate/all_tracts_demographics.csv"
        )

        # Step 5: Multi-radius population analysis with complete tract data
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5: Multi-Radius Population Analysis (with Area-Weighting)")
        logger.info("=" * 80)

        # Create population lookup from ALL collected demographics
        pop_lookup = all_tracts_with_demographics[['census_geoid', 'total_population']].copy()
        pop_lookup = pop_lookup.rename(columns={'census_geoid': 'GEOID', 'total_population': 'B01001_001E'})
        pop_lookup['GEOID'] = pop_lookup['GEOID'].astype(str)
        pop_lookup = pop_lookup.dropna()

        logger.info(f"Population lookup contains {len(pop_lookup)} tracts with data")

        # Calculate multi-radius populations
        for idx, row in dispensaries_df.iterrows():
            lat = row.get('latitude')
            lon = row.get('longitude')
            state = row.get('state_abbr')

            if pd.isna(lat) or pd.isna(lon) or pd.isna(state):
                continue

            try:
                pop_data = analyzer.calculate_multi_radius_population(
                    lat, lon, state, pop_lookup
                )

                # Update DataFrame
                for radius in [1, 3, 5, 10, 20]:
                    dispensaries_df.at[idx, f'pop_{radius}mi'] = pop_data[f'pop_{radius}mi']

            except Exception as e:
                logger.error(f"Error calculating populations for row {idx}: {e}")
                continue

            # Progress
            if (idx + 1) % 25 == 0:
                logger.info(f"Processed {idx + 1}/{len(dispensaries_df)} dispensaries")

        # Save checkpoint
        logger.info("Saving multi-radius population checkpoint")
        dispensaries_df.to_csv("data/census/intermediate/populations_calculated.csv", index=False)

        # Step 6: Add tract areas to dispensary data for density calculation
        logger.info("\n" + "=" * 80)
        logger.info("STEP 6: Adding Tract Areas for Density Calculation")
        logger.info("=" * 80)

        # Create area lookup from home tracts
        home_tract_areas = all_tracts_with_demographics[['census_geoid', 'tract_area_sqm']].copy()
        home_tract_areas = home_tract_areas.drop_duplicates(subset='census_geoid')

        # Ensure census_geoid is string type in both dataframes
        dispensaries_df['census_geoid'] = dispensaries_df['census_geoid'].astype(str)
        home_tract_areas['census_geoid'] = home_tract_areas['census_geoid'].astype(str)

        # Merge tract areas into dispensary data
        dispensaries_df = dispensaries_df.merge(
            home_tract_areas,
            on='census_geoid',
            how='left'
        )

        areas_present = dispensaries_df['tract_area_sqm'].notna().sum()
        logger.info(f"Tract areas available for {areas_present}/{len(dispensaries_df)} dispensaries")

        # Step 7: Feature engineering
        logger.info("\n" + "=" * 80)
        logger.info("STEP 7: Feature Engineering")
        logger.info("=" * 80)

        engineer = CensusFeatureEngineer()
        dispensaries_df = engineer.engineer_features(dispensaries_df)

        # Save checkpoint
        logger.info("Saving engineered features checkpoint")
        dispensaries_df.to_csv("data/census/intermediate/features_engineered.csv", index=False)

        # Step 8: Data integration
        logger.info("\n" + "=" * 80)
        logger.info("STEP 8: Data Integration")
        logger.info("=" * 80)

        integrator = CensusDataIntegrator()

        # Split back to FL and PA
        fl_census = dispensaries_df[dispensaries_df['state_abbr'] == 'FL'].copy()
        pa_census = dispensaries_df[dispensaries_df['state_abbr'] == 'PA'].copy()

        logger.info(f"\nFL dispensaries with census data: {len(fl_census)}")
        logger.info(f"PA dispensaries with census data: {len(pa_census)}")

        # Load original combined datasets and add dispensary_id
        fl_original = pd.read_csv("data/processed/FL_combined_dataset_current.csv")
        fl_original['dispensary_id'] = ['FL_' + str(i).zfill(4) for i in range(len(fl_original))]

        pa_original = pd.read_csv("data/processed/PA_combined_dataset_current.csv")
        pa_original['dispensary_id'] = ['PA_' + str(i).zfill(4) for i in range(len(pa_original))]

        # Integrate FL
        logger.info("\nIntegrating FL census data")
        fl_integrated = integrator.integrate_census_data(
            fl_original,
            fl_census,
            join_key='dispensary_id'
        )

        # Integrate PA
        logger.info("\nIntegrating PA census data")
        pa_integrated = integrator.integrate_census_data(
            pa_original,
            pa_census,
            join_key='dispensary_id'
        )

        # Validate
        logger.info("\n" + "=" * 80)
        logger.info("STEP 9: Validation")
        logger.info("=" * 80)

        logger.info("\nValidating FL integration:")
        fl_validation = integrator.validate_integration(fl_integrated)

        logger.info("\nValidating PA integration:")
        pa_validation = integrator.validate_integration(pa_integrated)

        # Save results
        logger.info("\n" + "=" * 80)
        logger.info("STEP 10: Saving Results")
        logger.info("=" * 80)

        if not args.sample:
            # Save updated datasets (with archive)
            integrator.save_updated_dataset(
                fl_integrated,
                "data/processed/FL_combined_dataset_current.csv",
                archive_original=True
            )

            integrator.save_updated_dataset(
                pa_integrated,
                "data/processed/PA_combined_dataset_current.csv",
                archive_original=True
            )

            # Generate reports
            integrator.generate_summary_report(
                fl_validation,
                "data/census/FL_census_integration_report.json"
            )

            integrator.generate_summary_report(
                pa_validation,
                "data/census/PA_census_integration_report.json"
            )
        else:
            # Sample mode - save to different files
            fl_integrated.to_csv("data/census/FL_census_sample.csv", index=False)
            pa_integrated.to_csv("data/census/PA_census_sample.csv", index=False)
            logger.info("Sample results saved to data/census/*_census_sample.csv")

        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("CENSUS DATA COLLECTION COMPLETE")
        logger.info("=" * 80)

        total_training = len(dispensaries_df)
        fl_complete = fl_validation['census_complete']
        pa_complete = pa_validation['census_complete']
        total_complete = fl_complete + pa_complete

        logger.info(f"\nTraining dispensaries processed: {total_training}")
        logger.info(f"  FL complete: {fl_complete}/{len(fl_census)} ({fl_complete/len(fl_census)*100:.1f}%)")
        logger.info(f"  PA complete: {pa_complete}/{len(pa_census)} ({pa_complete/len(pa_census)*100:.1f}%)")
        logger.info(f"  Total complete: {total_complete}/{total_training} ({total_complete/total_training*100:.1f}%)")

        logger.info("\n✅ Phase 2 Census Demographics Integration complete!")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
