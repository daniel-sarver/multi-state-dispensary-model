#!/usr/bin/env python3
"""
Multi-State Dispensary Data Consolidation Script
===============================================

Extracts and consolidates Placer data for PA & FL dispensaries from existing sources.
Combines data from the PA dispensary model and US dispensary datasets to create
a unified multi-state dataset for enhanced modeling.

Data Sources:
- PA Dispensary Model: Existing PA dispensary data with traffic analysis
- US Dispensary Data: National Placer data including FL dispensaries

Features:
- Data validation and quality checks
- Coordinate boundary validation
- Duplicate detection and handling
- Comprehensive data integration

Usage:
    python3 consolidate_placer_data.py

Author: Daniel & Claude AI
Date: October 2025
Version: 1.0 (Initial Multi-State Integration)
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiStatePlacerConsolidator:
    """Consolidates Placer data from PA and FL sources into unified dataset."""

    def __init__(self):
        self.version = "v1.0"
        self.processing_date = datetime.now().strftime("%Y-%m-%d")
        self.project_root = Path(__file__).parent.parent.parent
        self.source_paths = {
            'pa_dispensaries': '/Users/daniel_insa/Claude/pa-dispensary-model/data/processed/PA_Dispensaries_With_Traffic.csv',
            'pa_final': '/Users/daniel_insa/Claude/us-dispensary-model/Data/PA Dispensaries/PA_Dispensaries_FINAL.csv',
            'us_dispensaries': '/Users/daniel_insa/Claude/pa-dispensary-model/data/external/us_dispensary_data.csv'
        }

        # State coordinate boundaries for validation
        self.state_bounds = {
            'PA': {'lat_min': 39.5, 'lat_max': 42.5, 'lon_min': -80.5, 'lon_max': -74.5},
            'FL': {'lat_min': 24.5, 'lat_max': 31.0, 'lon_min': -87.5, 'lon_max': -80.0}
        }

        logger.info(f"🚀 Multi-State Placer Consolidator {self.version}")
        logger.info("=" * 60)

    def load_source_data(self):
        """Load all source datasets with error handling."""
        logger.info("📥 Loading source datasets...")

        datasets = {}

        try:
            # Load PA dispensary data (existing model data)
            logger.info("Loading PA dispensary model data...")
            datasets['pa_model'] = pd.read_csv(self.source_paths['pa_dispensaries'])
            logger.info(f"✅ PA model data: {len(datasets['pa_model'])} dispensaries")

            # Load PA final dataset (comprehensive)
            logger.info("Loading PA comprehensive dataset...")
            datasets['pa_comprehensive'] = pd.read_csv(self.source_paths['pa_final'])
            logger.info(f"✅ PA comprehensive: {len(datasets['pa_comprehensive'])} dispensaries")

            # Load US national dataset
            logger.info("Loading US national dataset...")
            datasets['us_national'] = pd.read_csv(self.source_paths['us_dispensaries'])
            logger.info(f"✅ US national data: {len(datasets['us_national'])} dispensaries")

            return datasets

        except Exception as e:
            logger.error(f"❌ Error loading source data: {str(e)}")
            raise

    def extract_state_data(self, us_data, state_code):
        """Extract dispensaries for specific state from US dataset."""
        logger.info(f"🔍 Extracting {state_code} dispensaries from US dataset...")

        # Filter for specific state
        state_data = us_data[us_data['State Code'] == state_code].copy()

        logger.info(f"✅ Found {len(state_data)} {state_code} dispensaries in US dataset")
        return state_data

    def validate_coordinates(self, df, state_code):
        """Validate coordinates are within state boundaries."""
        logger.info(f"📍 Validating {state_code} coordinates...")

        bounds = self.state_bounds[state_code]

        # Check latitude bounds (use standardized column names)
        lat_valid = (df['latitude'] >= bounds['lat_min']) & (df['latitude'] <= bounds['lat_max'])

        # Check longitude bounds (use standardized column names)
        lon_valid = (df['longitude'] >= bounds['lon_min']) & (df['longitude'] <= bounds['lon_max'])

        # Combine validation
        valid_coords = lat_valid & lon_valid

        invalid_count = (~valid_coords).sum()
        if invalid_count > 0:
            logger.warning(f"⚠️  {invalid_count} dispensaries have coordinates outside {state_code} bounds")

        logger.info(f"✅ {valid_coords.sum()} dispensaries have valid {state_code} coordinates")

        return valid_coords

    def standardize_columns(self, df, source_type):
        """Standardize column names across different datasets."""
        logger.info(f"🔄 Standardizing columns for {source_type} data...")

        # Define column mapping for different sources
        column_mappings = {
            'us_national': {
                'Property Name': 'dispensary_name',
                'Address': 'address',
                'City': 'city',
                'State Code': 'state',
                'Zip Code': 'zip_code',
                'Latitude': 'latitude',
                'Longitude': 'longitude',
                'Visits': 'est_visits',
                'sq ft': 'sq_ft',
                'Visits / sq ft': 'visits_per_sq_ft'
            },
            'pa_model': {
                'Property Name': 'dispensary_name',
                'Address': 'address',
                'City': 'city',
                'State': 'state',
                'Zip Code': 'zip_code',
                'Latitude': 'latitude',
                'Longitude': 'longitude',
                'Est. Visits': 'est_visits',
                'Sq Ft': 'sq_ft',
                'Visits / Sq Ft': 'visits_per_sq_ft',
                'County': 'county',
                'Region': 'region',
                'Placer_AADT': 'aadt'
            },
            'pa_comprehensive': {
                'Property Name': 'dispensary_name',
                'Address': 'address',
                'City': 'city',
                'State': 'state',
                'Zip Code': 'zip_code',
                'Latitude': 'latitude',
                'Longitude': 'longitude',
                'Est. Visits': 'est_visits',
                'Sq Ft': 'sq_ft',
                'Visits / Sq Ft': 'visits_per_sq_ft',
                'County': 'county',
                'Region': 'region',
                'License Type': 'license_type'
            }
        }

        if source_type in column_mappings:
            mapping = column_mappings[source_type]

            # Only rename columns that exist in the dataframe
            available_columns = {old: new for old, new in mapping.items() if old in df.columns}
            df_standardized = df.rename(columns=available_columns)

            logger.info(f"✅ Standardized {len(available_columns)} columns for {source_type}")
            return df_standardized
        else:
            logger.warning(f"⚠️  No column mapping defined for {source_type}")
            return df

    def clean_visit_data(self, df):
        """Clean and standardize visit data formats."""
        logger.info("🧹 Cleaning visit data...")

        if 'est_visits' in df.columns:
            # Remove commas and quotes from visit numbers
            df['est_visits'] = df['est_visits'].astype(str).str.replace(',', '').str.replace('"', '').str.replace(' ', '')

            # Convert to numeric, handling errors
            df['est_visits'] = pd.to_numeric(df['est_visits'], errors='coerce')

            # Log cleaning results
            valid_visits = df['est_visits'].notna().sum()
            logger.info(f"✅ {valid_visits} dispensaries have valid visit data")

        return df

    def consolidate_datasets(self, datasets):
        """Consolidate all datasets into unified multi-state dataset."""
        logger.info("🔄 Consolidating datasets into unified multi-state dataset...")

        consolidated_dfs = []

        # Extract and process FL data from US dataset
        fl_data = self.extract_state_data(datasets['us_national'], 'FL')
        fl_data = self.standardize_columns(fl_data, 'us_national')
        fl_data = self.clean_visit_data(fl_data)

        # Validate FL coordinates
        fl_valid_coords = self.validate_coordinates(fl_data, 'FL')
        fl_data = fl_data[fl_valid_coords].copy()
        fl_data['source'] = 'us_national_fl'

        consolidated_dfs.append(fl_data)
        logger.info(f"✅ Added {len(fl_data)} FL dispensaries")

        # Extract and process PA data from US dataset
        pa_us_data = self.extract_state_data(datasets['us_national'], 'PA')
        pa_us_data = self.standardize_columns(pa_us_data, 'us_national')
        pa_us_data = self.clean_visit_data(pa_us_data)

        # Validate PA coordinates
        pa_us_valid_coords = self.validate_coordinates(pa_us_data, 'PA')
        pa_us_data = pa_us_data[pa_us_valid_coords].copy()
        pa_us_data['source'] = 'us_national_pa'

        consolidated_dfs.append(pa_us_data)
        logger.info(f"✅ Added {len(pa_us_data)} PA dispensaries from US dataset")

        # Process PA model data (enhanced with traffic data)
        pa_model_data = self.standardize_columns(datasets['pa_model'], 'pa_model')
        pa_model_data = self.clean_visit_data(pa_model_data)

        # Only include dispensaries with valid visit data
        pa_model_valid = pa_model_data[pa_model_data['est_visits'].notna()].copy()
        pa_model_valid['source'] = 'pa_model_enhanced'

        consolidated_dfs.append(pa_model_valid)
        logger.info(f"✅ Added {len(pa_model_valid)} PA dispensaries from enhanced model data")

        # Combine all datasets
        consolidated_df = pd.concat(consolidated_dfs, ignore_index=True, sort=False)

        logger.info(f"🎯 Total consolidated dataset: {len(consolidated_df)} dispensaries")
        logger.info(f"📊 FL dispensaries: {len(consolidated_df[consolidated_df['state'] == 'FL'])}")
        logger.info(f"📊 PA dispensaries: {len(consolidated_df[consolidated_df['state'] == 'PA'])}")

        return consolidated_df

    def remove_duplicates(self, df):
        """Remove duplicate dispensaries using address and coordinates."""
        logger.info("🔍 Checking for and removing duplicates...")

        initial_count = len(df)

        # Create a standardized address for comparison
        df['address_standardized'] = df['address'].str.upper().str.replace(r'[^A-Z0-9]', '', regex=True)

        # Sort by source priority (enhanced PA model data first)
        source_priority = {'pa_model_enhanced': 1, 'us_national_fl': 2, 'us_national_pa': 3}
        df['source_priority'] = df['source'].map(source_priority).fillna(999)
        df = df.sort_values(['source_priority', 'est_visits'], ascending=[True, False])

        # Remove duplicates based on standardized address and coordinates
        df_deduped = df.drop_duplicates(
            subset=['address_standardized', 'city', 'state'],
            keep='first'
        )

        # Clean up temporary columns
        df_deduped = df_deduped.drop(['address_standardized', 'source_priority'], axis=1)

        duplicates_removed = initial_count - len(df_deduped)
        logger.info(f"✅ Removed {duplicates_removed} duplicates")
        logger.info(f"📊 Final dataset: {len(df_deduped)} unique dispensaries")

        return df_deduped

    def generate_quality_report(self, df):
        """Generate comprehensive data quality report."""
        logger.info("📋 Generating data quality report...")

        quality_metrics = {
            'total_dispensaries': int(len(df)),
            'fl_dispensaries': int(len(df[df['state'] == 'FL'])),
            'pa_dispensaries': int(len(df[df['state'] == 'PA'])),
            'dispensaries_with_visits': int(df['est_visits'].notna().sum()),
            'dispensaries_with_coordinates': int((df['latitude'].notna() & df['longitude'].notna()).sum()),
            'dispensaries_with_sq_ft': int(df['sq_ft'].notna().sum()) if 'sq_ft' in df.columns else 0,
            'visit_data_completeness': f"{(df['est_visits'].notna().sum() / len(df) * 100):.1f}%",
            'coordinate_completeness': f"{((df['latitude'].notna() & df['longitude'].notna()).sum() / len(df) * 100):.1f}%"
        }

        # Visit statistics (convert to Python int for JSON serialization)
        visit_data = df['est_visits'].dropna()
        if len(visit_data) > 0:
            quality_metrics.update({
                'avg_visits': int(float(visit_data.mean())),
                'median_visits': int(float(visit_data.median())),
                'min_visits': int(float(visit_data.min())),
                'max_visits': int(float(visit_data.max()))
            })

        # Source breakdown
        source_breakdown = df['source'].value_counts().to_dict()
        quality_metrics['source_breakdown'] = source_breakdown

        return quality_metrics

    def save_consolidated_data(self, df, quality_metrics):
        """Save consolidated dataset and quality metrics."""
        logger.info("💾 Saving consolidated dataset...")

        # Ensure output directories exist
        output_dir = self.project_root / 'data' / 'processed'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save main dataset
        main_output_path = output_dir / f'multi_state_dispensaries_{self.processing_date}.csv'
        df.to_csv(main_output_path, index=False)

        # Also save as current version (for consistent reference)
        current_output_path = output_dir / 'multi_state_dispensaries_current.csv'
        df.to_csv(current_output_path, index=False)

        # Save quality metrics
        quality_output_path = output_dir / f'data_quality_report_{self.processing_date}.json'
        quality_metrics['processing_date'] = self.processing_date
        quality_metrics['version'] = self.version

        with open(quality_output_path, 'w') as f:
            json.dump(quality_metrics, f, indent=2)

        logger.info(f"✅ Consolidated dataset saved: {main_output_path}")
        logger.info(f"✅ Current reference saved: {current_output_path}")
        logger.info(f"✅ Quality report saved: {quality_output_path}")

        return main_output_path, quality_output_path

    def run_consolidation(self):
        """Execute complete data consolidation process."""
        logger.info("🚀 Starting multi-state data consolidation...")

        try:
            # Load source datasets
            datasets = self.load_source_data()

            # Consolidate datasets
            consolidated_df = self.consolidate_datasets(datasets)

            # Remove duplicates
            final_df = self.remove_duplicates(consolidated_df)

            # Generate quality report
            quality_metrics = self.generate_quality_report(final_df)

            # Save results
            main_path, quality_path = self.save_consolidated_data(final_df, quality_metrics)

            # Print summary
            logger.info("=" * 60)
            logger.info("🎯 CONSOLIDATION COMPLETE - SUMMARY")
            logger.info("=" * 60)
            logger.info(f"📊 Total Dispensaries: {quality_metrics['total_dispensaries']}")
            logger.info(f"🌴 Florida: {quality_metrics['fl_dispensaries']} dispensaries")
            logger.info(f"🏛️  Pennsylvania: {quality_metrics['pa_dispensaries']} dispensaries")
            logger.info(f"📈 Visit Data: {quality_metrics['visit_data_completeness']} complete")
            logger.info(f"📍 Coordinates: {quality_metrics['coordinate_completeness']} complete")
            logger.info(f"💾 Output: {main_path.name}")
            logger.info("=" * 60)

            return final_df, quality_metrics

        except Exception as e:
            logger.error(f"❌ Consolidation failed: {str(e)}")
            raise

def main():
    """Main execution function."""
    consolidator = MultiStatePlacerConsolidator()
    consolidated_df, quality_metrics = consolidator.run_consolidation()

    print("\n🎉 Multi-state Placer data consolidation completed successfully!")
    print(f"📁 Check data/processed/ directory for output files")

if __name__ == "__main__":
    main()