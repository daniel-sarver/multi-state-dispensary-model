#!/usr/bin/env python3
"""
Multi-State Combined Dataset Creator
===================================

Creates comprehensive combined datasets for PA & FL using regulator data as source of truth
and integrating Placer data where available. Filters hemp/CBD stores from both states.

Key Features:
- Regulator data as authoritative source (complete competitive landscape)
- Placer data matched and integrated (training data subset)
- Hemp/CBD store filtering for both PA & FL
- Address-based matching with confidence scoring
- Proper flagging for training vs competition-only use

Usage:
    python3 create_combined_datasets.py

Author: Daniel & Claude AI
Date: October 2025
Version: 1.0 (Integrated State Processing)
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from datetime import datetime
import logging
from fuzzywuzzy import fuzz, process
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiStateCombinedProcessor:
    """Creates combined datasets for PA & FL using regulator + Placer data integration."""

    def __init__(self):
        self.version = "v1.0"
        self.processing_date = datetime.now().strftime("%Y-%m-%d")
        self.project_root = Path(__file__).parent.parent.parent

        # Data file paths
        self.data_files = {
            'fl_placer': 'data/raw/FL_Placer Data_Oct 1, 2024-Sep 30, 2025_10.22.25.csv',
            'pa_placer': 'data/raw/PA_Placer Data_Oct 1, 2024-Sep 30, 2025_10.22.csv',
            'fl_regulator': 'data/raw/FL_Regulator License Data_Final License_10.22.25.csv',
            'pa_regulator': 'data/raw/PA_Regulator License Data_Final License_10.22.25.csv',
            'pa_act63': 'data/raw/PA_Regulator License Data_Act 63 Licenses_10.22.25.csv'
        }

        # State coordinate boundaries for validation
        self.state_bounds = {
            'PA': {'lat_min': 39.5, 'lat_max': 42.5, 'lon_min': -80.5, 'lon_max': -74.5},
            'FL': {'lat_min': 24.5, 'lat_max': 31.0, 'lon_min': -87.5, 'lon_max': -80.0}
        }

        logger.info(f"🚀 Multi-State Combined Dataset Processor {self.version}")
        logger.info("=" * 70)

    def load_datasets(self):
        """Load all source datasets with comprehensive error handling."""
        logger.info("📥 Loading source datasets...")
        datasets = {}

        try:
            # Load FL datasets
            logger.info("Loading FL Placer data...")
            datasets['fl_placer'] = pd.read_csv(self.project_root / self.data_files['fl_placer'])
            logger.info(f"✅ FL Placer: {len(datasets['fl_placer'])} records")

            logger.info("Loading FL regulator data...")
            datasets['fl_regulator'] = pd.read_csv(self.project_root / self.data_files['fl_regulator'])
            logger.info(f"✅ FL Regulator: {len(datasets['fl_regulator'])} records")

            # Load PA datasets
            logger.info("Loading PA Placer data...")
            datasets['pa_placer'] = pd.read_csv(self.project_root / self.data_files['pa_placer'])
            logger.info(f"✅ PA Placer: {len(datasets['pa_placer'])} records")

            logger.info("Loading PA regulator data...")
            datasets['pa_regulator'] = pd.read_csv(self.project_root / self.data_files['pa_regulator'])
            logger.info(f"✅ PA Regulator: {len(datasets['pa_regulator'])} records")

            logger.info("Loading PA Act 63 data...")
            datasets['pa_act63'] = pd.read_csv(self.project_root / self.data_files['pa_act63'])
            logger.info(f"✅ PA Act 63: {len(datasets['pa_act63'])} records")

            return datasets

        except Exception as e:
            logger.error(f"❌ Error loading datasets: {str(e)}")
            raise

    def filter_cannabis_only(self, placer_df, state_code):
        """Filter Placer data to cannabis dispensaries only, removing hemp/CBD stores.

        Uses a whitelist approach for known cannabis chains plus category-based filtering
        to avoid excluding real dispensaries like Surterra Wellness or Ayr Wellness.
        """
        logger.info(f"🧹 Filtering {state_code} Placer data for cannabis dispensaries only...")

        initial_count = len(placer_df)

        # Primary filtering: Placer category must be cannabis
        cannabis_criteria = (
            (placer_df['Sub Category'] == 'Marijuana Dispensary') &
            (placer_df['Category'] == 'Medical & Recreational Cannabis Dispensaries')
        )

        # Known cannabis chains that might have misleading names (whitelist)
        cannabis_chains = [
            'trulieve', 'curaleaf', 'surterra', 'muv', 'vidacann', 'liberty',
            'fluent', 'growhealthy', 'rise', 'ayr', 'restore wellness',
            'sanctuary', 'cookies', 'insa', 'green dragon', 'jungle boys',
            'cannabist', 'columbia care'
        ]

        # Check if name contains known cannabis brand
        is_known_cannabis = placer_df['Property Name'].str.lower().str.contains(
            '|'.join(cannabis_chains), na=False
        )

        # Hemp/CBD exclusion keywords (only apply if NOT a known cannabis brand)
        hemp_cbd_keywords = [
            r'\bhemp\b', r'\bcbd\b', r'\bkratom\b', 'smoke shop', 'tobacco',
            'vape shop', 'head shop'
        ]

        # Flag potential hemp/CBD stores
        potential_hemp_cbd = placer_df['Property Name'].str.lower().str.contains(
            '|'.join(hemp_cbd_keywords), na=False, regex=True
        )

        # Keep if: (cannabis category AND (known cannabis brand OR not hemp/CBD flagged))
        cannabis_only = placer_df[
            cannabis_criteria & (is_known_cannabis | ~potential_hemp_cbd)
        ].copy()

        filtered_count = initial_count - len(cannabis_only)
        logger.info(f"✅ {state_code} filtering complete:")
        logger.info(f"   📊 Kept: {len(cannabis_only)} cannabis dispensaries")
        logger.info(f"   🗑️  Filtered: {filtered_count} hemp/CBD/other stores")
        logger.info(f"   📈 Cannabis rate: {(len(cannabis_only)/initial_count)*100:.1f}%")

        return cannabis_only

    def standardize_address(self, address):
        """Standardize address format for matching."""
        if pd.isna(address):
            return ""

        # Convert to uppercase and remove extra whitespace
        addr = str(address).upper().strip()

        # Standard abbreviations
        replacements = {
            r'\bSTREET\b': 'ST',
            r'\bROAD\b': 'RD',
            r'\bAVENUE\b': 'AVE',
            r'\bBOULEVARD\b': 'BLVD',
            r'\bDRIVE\b': 'DR',
            r'\bLANE\b': 'LN',
            r'\bCIRCLE\b': 'CIR',
            r'\bCOURT\b': 'CT',
            r'\bPLACE\b': 'PL',
            r'\bNORTH\b': 'N',
            r'\bSOUTH\b': 'S',
            r'\bEAST\b': 'E',
            r'\bWEST\b': 'W'
        }

        for pattern, replacement in replacements.items():
            addr = re.sub(pattern, replacement, addr)

        # Remove non-alphanumeric except spaces
        addr = re.sub(r'[^A-Z0-9\s]', '', addr)

        # Remove extra spaces
        addr = re.sub(r'\s+', ' ', addr).strip()

        return addr

    def calculate_match_score(self, placer_row, reg_row, address_col):
        """Calculate comprehensive match score including address, city, and ZIP."""
        placer_addr = placer_row['address_std']
        reg_addr = reg_row['address_std']

        # Address similarity (most important)
        addr_score = fuzz.ratio(placer_addr, reg_addr)

        # City similarity
        placer_city = str(placer_row['City']).upper().strip()
        reg_city_col = 'CITY' if 'CITY' in reg_row else 'City'
        reg_city = str(reg_row[reg_city_col]).upper().strip()
        city_score = fuzz.ratio(placer_city, reg_city)

        # ZIP similarity (exact match or close)
        placer_zip = str(placer_row['Zip Code']).strip()[:5]
        reg_zip_col = 'ZIP CODE' if 'ZIP CODE' in reg_row else 'Zip Code'
        reg_zip = str(reg_row[reg_zip_col]).strip()[:5]
        zip_match = 100 if placer_zip == reg_zip else 0

        # Weighted composite score: 60% address, 25% city, 15% ZIP
        composite_score = (addr_score * 0.60) + (city_score * 0.25) + (zip_match * 0.15)

        return {
            'composite': composite_score,
            'address': addr_score,
            'city': city_score,
            'zip': zip_match
        }

    def match_placer_to_regulator(self, placer_df, regulator_df, state_code):
        """Match Placer data to regulator data using enhanced address+city+ZIP matching.

        Uses composite scoring and allows multiple regulator candidates to avoid
        incorrectly dropping regulator records on first match.
        """
        logger.info(f"🔗 Matching {state_code} Placer data to regulator records...")

        matches = []
        unmatched_placer = []
        matched_regulator_indices = set()

        # Standardize addresses for matching
        placer_df['address_std'] = placer_df['Address'].apply(self.standardize_address)

        # Handle different regulator address column names
        if 'ADDRESS' in regulator_df.columns:
            address_col = 'ADDRESS'
        elif 'Address' in regulator_df.columns:
            address_col = 'Address'
        else:
            logger.error(f"❌ No address column found in {state_code} regulator data")
            return pd.DataFrame(), placer_df.copy(), regulator_df

        regulator_df['address_std'] = regulator_df[address_col].apply(self.standardize_address)

        # Create working copy to preserve original
        working_regulator_df = regulator_df.copy()

        for idx, placer_row in placer_df.iterrows():
            best_match = None
            best_scores = None
            best_composite = 0

            placer_addr = placer_row['address_std']
            if not placer_addr:
                unmatched_placer.append(placer_row)
                continue

            # Try exact address match first (quick path)
            exact_matches = working_regulator_df[
                (working_regulator_df['address_std'] == placer_addr) &
                (~working_regulator_df.index.isin(matched_regulator_indices))
            ]

            if len(exact_matches) > 0:
                # If multiple exact matches, use city/ZIP to disambiguate
                for reg_idx, reg_row in exact_matches.iterrows():
                    scores = self.calculate_match_score(placer_row, reg_row, address_col)
                    if scores['composite'] > best_composite:
                        best_composite = scores['composite']
                        best_scores = scores
                        best_match = (reg_idx, reg_row)
            else:
                # Fuzzy matching with composite scoring
                for reg_idx, reg_row in working_regulator_df.iterrows():
                    if reg_idx in matched_regulator_indices:
                        continue

                    scores = self.calculate_match_score(placer_row, reg_row, address_col)

                    # Require minimum thresholds
                    if scores['address'] >= 75 and scores['composite'] >= 80:
                        if scores['composite'] > best_composite:
                            best_composite = scores['composite']
                            best_scores = scores
                            best_match = (reg_idx, reg_row)

            if best_match is not None:
                reg_idx, matched_reg_row = best_match

                # Determine match type
                if best_scores['address'] == 100 and best_scores['zip'] == 100:
                    match_type = 'exact'
                else:
                    match_type = 'fuzzy'

                # Create matched record
                matched_record = {
                    'state': state_code,
                    'data_source': 'regulator_with_placer',
                    'has_placer_data': True,
                    'match_score': round(best_composite, 1),
                    'match_type': match_type,
                    'match_details': f"addr:{best_scores['address']:.0f}|city:{best_scores['city']:.0f}|zip:{best_scores['zip']:.0f}",

                    # Regulator data (source of truth)
                    'regulator_name': matched_reg_row.get('COMPANY', matched_reg_row.get('Dispensary name', '')),
                    'regulator_address': matched_reg_row.get(address_col, ''),
                    'regulator_city': matched_reg_row.get('CITY', matched_reg_row.get('City', '')),
                    'regulator_zip': matched_reg_row.get('ZIP CODE', matched_reg_row.get('Zip Code', '')),
                    'regulator_county': matched_reg_row.get('COUNTY', matched_reg_row.get('County', '')),

                    # Placer data (training features)
                    'placer_name': placer_row['Property Name'],
                    'placer_address': placer_row['Address'],
                    'placer_city': placer_row['City'],
                    'placer_zip': placer_row['Zip Code'],
                    'latitude': placer_row['Latitude'],
                    'longitude': placer_row['Longitude'],
                    'visits': placer_row['Visits'],
                    'sq_ft': placer_row['sq ft'],
                    'visits_per_sq_ft': placer_row['Visits / sq ft'],
                    'chain_name': placer_row.get('Chain Name', ''),
                    'chain_id': placer_row.get('Chain Id', '')
                }

                # Add PA-specific fields if available
                if state_code == 'PA' and 'Medical marijuana available beginning:' in matched_reg_row:
                    matched_record['opening_date'] = matched_reg_row['Medical marijuana available beginning:']
                    matched_record['operational_date'] = matched_reg_row['Open on:']
                    matched_record['product_available'] = matched_reg_row['Product available as of 10/14/2025:']

                matches.append(matched_record)
                matched_regulator_indices.add(reg_idx)
            else:
                unmatched_placer.append(placer_row)

        matches_df = pd.DataFrame(matches)
        unmatched_placer_df = pd.DataFrame(unmatched_placer) if unmatched_placer else pd.DataFrame()

        # Return only unmatched regulator records
        remaining_regulator_df = working_regulator_df[
            ~working_regulator_df.index.isin(matched_regulator_indices)
        ]

        logger.info(f"✅ {state_code} matching results:")
        logger.info(f"   🎯 Matched: {len(matches_df)} Placer records to regulator data")
        logger.info(f"   ❓ Unmatched Placer: {len(unmatched_placer_df)} records")
        logger.info(f"   📋 Remaining regulator: {len(remaining_regulator_df)} records")
        if len(matches_df) > 0:
            exact_matches = len(matches_df[matches_df['match_type'] == 'exact'])
            fuzzy_matches = len(matches_df[matches_df['match_type'] == 'fuzzy'])
            avg_score = matches_df['match_score'].mean()
            logger.info(f"   📍 Exact matches: {exact_matches}")
            logger.info(f"   🔍 Fuzzy matches: {fuzzy_matches}")
            logger.info(f"   📊 Average match score: {avg_score:.1f}")

        return matches_df, unmatched_placer_df, remaining_regulator_df

    def validate_coordinates(self, df, state_code):
        """Validate that coordinates fall within expected state boundaries."""
        if len(df) == 0:
            return df

        logger.info(f"🗺️  Validating {state_code} coordinates...")

        bounds = self.state_bounds[state_code]
        initial_count = len(df)

        # Filter to records with coordinates
        has_coords = df[df['latitude'].notna() & df['longitude'].notna()].copy()

        if len(has_coords) == 0:
            logger.info(f"   ℹ️  No coordinates to validate")
            return df

        # Check boundaries
        lat_valid = (has_coords['latitude'] >= bounds['lat_min']) & (has_coords['latitude'] <= bounds['lat_max'])
        lon_valid = (has_coords['longitude'] >= bounds['lon_min']) & (has_coords['longitude'] <= bounds['lon_max'])

        valid_coords = lat_valid & lon_valid
        invalid_count = (~valid_coords).sum()

        if invalid_count > 0:
            logger.warning(f"   ⚠️  Found {invalid_count} records with coordinates outside {state_code} boundaries")
            invalid_records = has_coords[~valid_coords][['placer_name', 'placer_address', 'latitude', 'longitude']]
            for idx, row in invalid_records.iterrows():
                logger.warning(f"      - {row['placer_name']}: ({row['latitude']:.4f}, {row['longitude']:.4f})")

            # Remove invalid coordinates (keep record but clear coordinates)
            df.loc[has_coords[~valid_coords].index, ['latitude', 'longitude']] = None
            logger.info(f"   🔧 Cleared {invalid_count} invalid coordinate pairs")

        valid_count = valid_coords.sum()
        logger.info(f"   ✅ Validated {valid_count} coordinate pairs within {state_code} boundaries")
        logger.info(f"      Lat: {bounds['lat_min']:.1f} to {bounds['lat_max']:.1f}")
        logger.info(f"      Lon: {bounds['lon_min']:.1f} to {bounds['lon_max']:.1f}")

        return df

    def add_regulator_only_records(self, remaining_regulator_df, state_code):
        """Add regulator-only records (no Placer data) for complete competitive landscape."""
        logger.info(f"📋 Adding {state_code} regulator-only records for complete competitive landscape...")

        regulator_only = []

        # Handle different regulator column structures
        if 'ADDRESS' in remaining_regulator_df.columns:
            # FL format
            address_col, city_col, zip_col, county_col = 'ADDRESS', 'CITY', 'ZIP CODE', 'COUNTY'
            name_col = 'COMPANY'
        else:
            # PA format
            address_col, city_col, zip_col = 'Address', 'City', 'Zip Code'
            county_col = 'County' if 'County' in remaining_regulator_df.columns else None
            name_col = 'Dispensary name'

        for idx, reg_row in remaining_regulator_df.iterrows():
            record = {
                'state': state_code,
                'data_source': 'regulator_only',
                'has_placer_data': False,
                'match_score': None,
                'match_type': None,

                # Regulator data
                'regulator_name': reg_row.get(name_col, ''),
                'regulator_address': reg_row.get(address_col, ''),
                'regulator_city': reg_row.get(city_col, ''),
                'regulator_zip': reg_row.get(zip_col, ''),
                'regulator_county': reg_row.get(county_col, '') if county_col else '',

                # Empty Placer fields
                'placer_name': '',
                'placer_address': '',
                'placer_city': '',
                'placer_zip': '',
                'latitude': None,
                'longitude': None,
                'visits': None,
                'sq_ft': None,
                'visits_per_sq_ft': None,
                'chain_name': '',
                'chain_id': ''
            }

            # Add PA-specific fields if available
            if state_code == 'PA' and 'Medical marijuana available beginning:' in reg_row:
                record['opening_date'] = reg_row['Medical marijuana available beginning:']
                record['operational_date'] = reg_row['Open on:']
                record['product_available'] = reg_row['Product available as of 10/14/2025:']

            regulator_only.append(record)

        regulator_only_df = pd.DataFrame(regulator_only)
        logger.info(f"✅ Added {len(regulator_only_df)} {state_code} regulator-only records")

        return regulator_only_df

    def process_state(self, datasets, state_code):
        """Process a complete state dataset (regulator + Placer integration)."""
        logger.info(f"🏛️ Processing {state_code} combined dataset...")

        # Filter Placer data for cannabis only
        if state_code == 'FL':
            filtered_placer = self.filter_cannabis_only(datasets['fl_placer'], state_code)
            regulator_data = datasets['fl_regulator']
        else:  # PA
            filtered_placer = self.filter_cannabis_only(datasets['pa_placer'], state_code)
            regulator_data = datasets['pa_regulator']

        # Match Placer to regulator data
        matched_df, unmatched_placer_df, remaining_regulator_df = self.match_placer_to_regulator(
            filtered_placer, regulator_data, state_code
        )

        # Validate coordinates for matched records
        matched_df = self.validate_coordinates(matched_df, state_code)

        # Add regulator-only records
        regulator_only_df = self.add_regulator_only_records(remaining_regulator_df, state_code)

        # Combine all records for complete state dataset
        combined_df = pd.concat([matched_df, regulator_only_df], ignore_index=True, sort=False)

        logger.info(f"🎯 {state_code} combined dataset complete:")
        logger.info(f"   📊 Total dispensaries: {len(combined_df)}")
        logger.info(f"   🎯 With Placer data: {len(combined_df[combined_df['has_placer_data']])} (training eligible)")
        logger.info(f"   📋 Regulator only: {len(combined_df[~combined_df['has_placer_data']])} (competition only)")

        return combined_df, unmatched_placer_df

    def add_act63_data(self, pa_combined_df, pa_act63_df):
        """Add PA Act 63 provisional licenses to PA dataset."""
        logger.info("📋 Adding PA Act 63 provisional licenses...")

        act63_records = []
        for idx, act63_row in pa_act63_df.iterrows():
            record = {
                'state': 'PA',
                'data_source': 'act63_provisional',
                'has_placer_data': False,
                'match_score': None,
                'match_type': None,

                # Act 63 data
                'regulator_name': act63_row['Provided Facility Name'],
                'regulator_address': act63_row['Address'],
                'regulator_city': act63_row['City'],
                'regulator_zip': act63_row['Zip Code'],
                'regulator_county': act63_row['County'],

                # Additional Act 63 fields
                'applicant_name': act63_row['Applicant Name'],
                'permit_number': act63_row['Permit Number*'],
                'region': act63_row['Region'],
                'license_type': 'Provisional',

                # Empty Placer fields
                'placer_name': '',
                'placer_address': '',
                'placer_city': '',
                'placer_zip': '',
                'latitude': None,
                'longitude': None,
                'visits': None,
                'sq_ft': None,
                'visits_per_sq_ft': None,
                'chain_name': '',
                'chain_id': ''
            }
            act63_records.append(record)

        act63_df = pd.DataFrame(act63_records)

        # Combine with main PA dataset
        pa_complete_df = pd.concat([pa_combined_df, act63_df], ignore_index=True, sort=False)

        logger.info(f"✅ Added {len(act63_df)} PA Act 63 provisional licenses")
        logger.info(f"📊 PA total dispensaries: {len(pa_complete_df)}")

        return pa_complete_df

    def generate_summary_report(self, fl_combined_df, pa_combined_df, fl_unmatched_df, pa_unmatched_df):
        """Generate comprehensive processing summary report."""
        logger.info("📋 Generating processing summary report...")

        # Calculate summary statistics
        fl_total = len(fl_combined_df)
        fl_with_placer = len(fl_combined_df[fl_combined_df['has_placer_data']])
        fl_regulator_only = fl_total - fl_with_placer

        pa_total = len(pa_combined_df)
        pa_with_placer = len(pa_combined_df[pa_combined_df['has_placer_data']])
        pa_regulator_only = pa_total - pa_with_placer
        pa_act63 = len(pa_combined_df[pa_combined_df['data_source'] == 'act63_provisional'])

        training_total = fl_with_placer + pa_with_placer
        competition_total = fl_total + pa_total

        summary = {
            'processing_date': self.processing_date,
            'version': self.version,

            'florida_summary': {
                'total_dispensaries': int(fl_total),
                'with_placer_data': int(fl_with_placer),
                'regulator_only': int(fl_regulator_only),
                'unmatched_placer': int(len(fl_unmatched_df)),
                'training_eligible_pct': f"{(fl_with_placer/fl_total)*100:.1f}%"
            },

            'pennsylvania_summary': {
                'total_dispensaries': int(pa_total),
                'with_placer_data': int(pa_with_placer),
                'regulator_only': int(pa_regulator_only),
                'act63_provisional': int(pa_act63),
                'unmatched_placer': int(len(pa_unmatched_df)),
                'training_eligible_pct': f"{(pa_with_placer/pa_total)*100:.1f}%"
            },

            'multi_state_totals': {
                'total_training_eligible': int(training_total),
                'total_competitive_landscape': int(competition_total),
                'training_vs_target': f"{training_total} dispensaries (target was ~750)",
                'data_coverage': f"{(training_total/competition_total)*100:.1f}% have training data"
            }
        }

        return summary

    def save_datasets(self, fl_combined_df, pa_combined_df, fl_unmatched_df, pa_unmatched_df, summary):
        """Save all processed datasets and reports."""
        logger.info("💾 Saving processed datasets...")

        # Ensure output directory exists
        output_dir = self.project_root / 'data' / 'processed'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save main combined datasets
        fl_output_path = output_dir / f'FL_combined_dataset_{self.processing_date}.csv'
        pa_output_path = output_dir / f'PA_combined_dataset_{self.processing_date}.csv'

        fl_combined_df.to_csv(fl_output_path, index=False)
        pa_combined_df.to_csv(pa_output_path, index=False)

        # Save current versions for easy reference
        fl_combined_df.to_csv(output_dir / 'FL_combined_dataset_current.csv', index=False)
        pa_combined_df.to_csv(output_dir / 'PA_combined_dataset_current.csv', index=False)

        # Save unmatched records for review
        if len(fl_unmatched_df) > 0:
            fl_unmatched_df.to_csv(output_dir / f'FL_unmatched_placer_{self.processing_date}.csv', index=False)
        if len(pa_unmatched_df) > 0:
            pa_unmatched_df.to_csv(output_dir / f'PA_unmatched_placer_{self.processing_date}.csv', index=False)

        # Save summary report
        summary_path = output_dir / f'processing_summary_{self.processing_date}.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"✅ Datasets saved:")
        logger.info(f"   📁 FL combined: {fl_output_path.name}")
        logger.info(f"   📁 PA combined: {pa_output_path.name}")
        logger.info(f"   📁 Summary: {summary_path.name}")

        return fl_output_path, pa_output_path, summary_path

    def run_processing(self):
        """Execute complete multi-state dataset processing."""
        logger.info("🚀 Starting multi-state combined dataset processing...")

        try:
            # Load all datasets
            datasets = self.load_datasets()

            # Process each state
            fl_combined_df, fl_unmatched_df = self.process_state(datasets, 'FL')
            pa_combined_df, pa_unmatched_df = self.process_state(datasets, 'PA')

            # Add PA Act 63 provisional licenses
            pa_combined_df = self.add_act63_data(pa_combined_df, datasets['pa_act63'])

            # Generate summary report
            summary = self.generate_summary_report(fl_combined_df, pa_combined_df, fl_unmatched_df, pa_unmatched_df)

            # Save all datasets
            fl_path, pa_path, summary_path = self.save_datasets(
                fl_combined_df, pa_combined_df, fl_unmatched_df, pa_unmatched_df, summary
            )

            # Print final summary
            logger.info("=" * 70)
            logger.info("🎯 MULTI-STATE PROCESSING COMPLETE")
            logger.info("=" * 70)
            logger.info(f"🌴 FLORIDA: {summary['florida_summary']['total_dispensaries']} total")
            logger.info(f"   📊 Training eligible: {summary['florida_summary']['with_placer_data']}")
            logger.info(f"   📋 Competition only: {summary['florida_summary']['regulator_only']}")
            logger.info(f"🏛️  PENNSYLVANIA: {summary['pennsylvania_summary']['total_dispensaries']} total")
            logger.info(f"   📊 Training eligible: {summary['pennsylvania_summary']['with_placer_data']}")
            logger.info(f"   📋 Competition only: {summary['pennsylvania_summary']['regulator_only']}")
            logger.info(f"   🚧 Provisional (Act 63): {summary['pennsylvania_summary']['act63_provisional']}")
            logger.info(f"🎯 MULTI-STATE TOTALS:")
            logger.info(f"   🎓 Training eligible: {summary['multi_state_totals']['total_training_eligible']}")
            logger.info(f"   🏆 Competitive landscape: {summary['multi_state_totals']['total_competitive_landscape']}")
            logger.info(f"   📈 Training coverage: {summary['multi_state_totals']['data_coverage']}")
            logger.info("=" * 70)

            return fl_combined_df, pa_combined_df, summary

        except Exception as e:
            logger.error(f"❌ Processing failed: {str(e)}")
            raise

def main():
    """Main execution function."""
    processor = MultiStateCombinedProcessor()
    fl_df, pa_df, summary = processor.run_processing()

    print("\n🎉 Multi-state combined dataset processing completed successfully!")
    print("📁 Check data/processed/ directory for output files")
    print(f"📊 Ready for enhanced model training with {summary['multi_state_totals']['total_training_eligible']} dispensaries!")

if __name__ == "__main__":
    main()