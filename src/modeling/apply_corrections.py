"""
Apply Placer Correction and FL Temporal Adjustments

Purpose: Create corrected dataset with:
  1. Placer calibration correction using Insa actual data
  2. FL temporal adjustments for sites <12 months operational

NAMING CONVENTION:
  - placer_visits: Original Placer ANNUAL visit estimates (uncorrected)
  - corrected_visits: ANNUAL visits after Placer correction and temporal adjustments
  - This script creates CORRECTED ANNUAL VISIT data for model training

IMPORTANT: Placer data represents ANNUAL visits, not monthly
  - Insa actual data is MONTHLY (April 2025 transactions)
  - Comparison requires dividing Placer annual by 12

Author: Claude Code
Date: October 24, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re


class DataCorrector:
    """Apply Placer and temporal corrections to dispensary visit data."""

    def __init__(self,
                 data_path='data/processed/combined_with_competitive_features.csv',
                 insa_kpi_path='Insa_April 2025 Retail KPIs.csv',
                 fl_openings_path='FL_Recent Openings_10.24.25.csv'):
        """Initialize data corrector."""
        self.data_path = data_path
        self.insa_kpi_path = insa_kpi_path
        self.fl_openings_path = fl_openings_path

        self.df = None
        self.insa_actual = None
        self.fl_openings = None
        self.placer_correction_factor = None

    def load_data(self):
        """Load main dataset."""
        print("Loading dispensary dataset...")
        self.df = pd.read_csv(self.data_path)

        # RENAME 'visits' to 'placer_visits' for clarity
        if 'visits' in self.df.columns and 'placer_visits' not in self.df.columns:
            self.df.rename(columns={'visits': 'placer_visits'}, inplace=True)
            print("  ✅ Renamed 'visits' → 'placer_visits'")

        print(f"  Total dispensaries: {len(self.df)}")
        print(f"  Training dispensaries: {self.df['has_placer_data'].sum()}")
        print()

    def load_insa_actual_data(self):
        """Load and extract Insa actual transaction data."""
        print("="*70)
        print("STEP 1: PLACER CORRECTION (Using Insa Actual Data)")
        print("="*70)
        print()

        # Import extraction function
        import sys
        sys.path.insert(0, 'src/modeling')
        from extract_insa_data import extract_insa_transactions

        # Extract April 2025 transactions
        self.insa_actual = extract_insa_transactions(self.insa_kpi_path, 'April', '2025')

        print()
        print("Insa Actual Data (April 2025):")
        print("-" * 70)
        for city, transactions in sorted(self.insa_actual.items()):
            print(f"  {city:20} | {transactions:>10,.0f} transactions")
        print()

    def match_insa_to_placer(self):
        """Match Insa stores to Placer data and calculate correction factor."""
        print("Matching Insa stores to Placer data...")
        print()
        print("⚠️  IMPORTANT: Placer 'visits' appear to be ANNUAL visits")
        print("   Converting to monthly for comparison with Insa April 2025 data")
        print()

        # Find Insa stores in dataset
        insa_mask = self.df['regulator_name'].str.contains('Insa', case=False, na=False)
        insa_placer = self.df[insa_mask & (self.df['has_placer_data'] == True)].copy()

        # Match by city
        matches = []
        for idx, row in insa_placer.iterrows():
            city = row['regulator_city']
            placer_visits_annual = row['placer_visits']
            placer_visits_monthly = placer_visits_annual / 12  # Convert to monthly

            # Try exact match
            if city in self.insa_actual:
                actual = self.insa_actual[city]
                matches.append({
                    'city': city,
                    'placer_annual': placer_visits_annual,
                    'placer_monthly': placer_visits_monthly,
                    'actual_monthly': actual,
                    'ratio': actual / placer_visits_monthly if placer_visits_monthly > 0 else None
                })
            # Try with _2 suffix (duplicate cities)
            elif f"{city}_2" in self.insa_actual:
                actual = self.insa_actual[f"{city}_2"]
                matches.append({
                    'city': f"{city} (2nd location)",
                    'placer_annual': placer_visits_annual,
                    'placer_monthly': placer_visits_monthly,
                    'actual_monthly': actual,
                    'ratio': actual / placer_visits_monthly if placer_visits_monthly > 0 else None
                })

        if len(matches) == 0:
            print("⚠️  No matches found between Insa and Placer data")
            print("   Check city name consistency")
            return None

        # Create comparison DataFrame
        comparison = pd.DataFrame(matches)

        print(f"Matched {len(comparison)} Insa stores:")
        print()
        print(comparison.to_string(index=False))
        print()

        # Calculate correction factor (monthly comparison)
        total_actual_monthly = comparison['actual_monthly'].sum()
        total_placer_monthly = comparison['placer_monthly'].sum()

        self.placer_correction_factor = total_actual_monthly / total_placer_monthly

        print("="*70)
        print("PLACER CORRECTION FACTOR CALCULATION (Monthly Comparison)")
        print("="*70)
        print(f"Total Insa actual monthly visits (April 2025): {total_actual_monthly:,.0f}")
        print(f"Total Insa Placer monthly visits (annual/12): {total_placer_monthly:,.0f}")
        print()
        print(f"Correction factor: {self.placer_correction_factor:.4f}")
        print()

        if self.placer_correction_factor > 1.0:
            pct_diff = (self.placer_correction_factor - 1) * 100
            print(f"✅ Placer UNDERESTIMATES monthly visits by {pct_diff:.1f}%")
        else:
            pct_diff = (1 - self.placer_correction_factor) * 100
            print(f"✅ Placer OVERESTIMATES monthly visits by {pct_diff:.1f}%")
        print()
        print("NOTE: This correction factor will be applied to ANNUAL Placer visits")
        print(f"      Corrected annual = Placer annual × {self.placer_correction_factor:.4f}")
        print()

        return comparison

    def apply_placer_correction(self):
        """Apply Placer correction factor to all training data."""
        print("Applying Placer correction to all training dispensaries...")
        print()

        training_mask = self.df['has_placer_data'] == True

        # Apply correction
        self.df.loc[training_mask, 'corrected_visits_step1'] = (
            self.df.loc[training_mask, 'placer_visits'] * self.placer_correction_factor
        )

        # For non-training data, keep NaN
        self.df.loc[~training_mask, 'corrected_visits_step1'] = np.nan

        print(f"✅ Applied correction factor {self.placer_correction_factor:.4f} to {training_mask.sum()} dispensaries")
        print()
        print("Before correction:")
        print(f"  Mean placer_visits: {self.df.loc[training_mask, 'placer_visits'].mean():,.0f}")
        print(f"  Median placer_visits: {self.df.loc[training_mask, 'placer_visits'].median():,.0f}")
        print()
        print("After Placer correction (Step 1):")
        print(f"  Mean corrected_visits: {self.df.loc[training_mask, 'corrected_visits_step1'].mean():,.0f}")
        print(f"  Median corrected_visits: {self.df.loc[training_mask, 'corrected_visits_step1'].median():,.0f}")
        print()

    def load_fl_openings(self):
        """Load FL recent openings data."""
        print("="*70)
        print("STEP 2: FL TEMPORAL ADJUSTMENTS (Sites <12 Months Old)")
        print("="*70)
        print()

        print("Loading FL recent openings data...")
        self.fl_openings = pd.read_csv(self.fl_openings_path)

        # Clean location names
        self.fl_openings['location_clean'] = (
            self.fl_openings['Location']
            .str.strip()
            .str.replace(r'\s+', ' ', regex=True)
        )

        print(f"  Total FL openings (Oct 2024 - Oct 2025): {len(self.fl_openings)}")
        print()

    def parse_opening_dates(self):
        """Parse opening week strings to dates."""
        print("Parsing opening dates...")

        # Data collection date (when Placer data was collected)
        data_collection_date = pd.to_datetime('2025-10-23')

        def parse_week(week_str):
            """Extract approximate opening date from week string."""
            # Format examples:
            # " October 14 - 18, 2024"
            # "October 28 – November 1, \n2024"
            # " January 27 – 31, 2025"

            # Extract year
            year_match = re.search(r'20\d{2}', week_str)
            if not year_match:
                return None
            year = int(year_match.group())

            # Extract first month
            months = ['January', 'February', 'March', 'April', 'May', 'June',
                     'July', 'August', 'September', 'October', 'November', 'December']

            month = None
            for m in months:
                if m in week_str:
                    month = months.index(m) + 1
                    break

            if month is None:
                return None

            # Extract first day number
            day_match = re.search(r'(\d{1,2})\s*[-–]', week_str)
            if not day_match:
                return None
            day = int(day_match.group(1))

            try:
                return pd.to_datetime(f'{year}-{month:02d}-{day:02d}')
            except:
                return None

        self.fl_openings['opening_date'] = self.fl_openings['Opening Week'].apply(parse_week)

        # Calculate months operational
        self.fl_openings['months_operational'] = (
            (data_collection_date - self.fl_openings['opening_date']).dt.days / 30.44
        )

        # Filter to sites with valid dates and <12 months
        valid_mask = self.fl_openings['opening_date'].notna()
        recent_mask = self.fl_openings['months_operational'] < 12

        self.fl_openings_recent = self.fl_openings[valid_mask & recent_mask].copy()

        print(f"  Parsed {valid_mask.sum()} opening dates successfully")
        print(f"  Sites <12 months operational: {len(self.fl_openings_recent)}")
        print()

        # Show distribution
        print("Distribution of months operational:")
        bins = [0, 3, 6, 9, 12]
        labels = ['0-3 months', '3-6 months', '6-9 months', '9-12 months']
        self.fl_openings_recent['maturity_bin'] = pd.cut(
            self.fl_openings_recent['months_operational'],
            bins=bins,
            labels=labels,
            include_lowest=True
        )
        print(self.fl_openings_recent['maturity_bin'].value_counts().sort_index())
        print()

    def match_openings_to_training_data(self):
        """Match FL openings to dispensaries in training dataset."""
        print("Matching FL openings to training dispensaries...")
        print()

        # FL training dispensaries only
        fl_training = self.df[
            (self.df['state'] == 'FL') &
            (self.df['has_placer_data'] == True)
        ].copy()

        print(f"  FL training dispensaries: {len(fl_training)}")
        print()

        # Try to match by location/city/brand
        matches = []

        for idx, opening in self.fl_openings_recent.iterrows():
            location_str = opening['location_clean']

            # Extract components
            # Format: "Brand - City" or "Brand, LLC - City"
            parts = location_str.split('–')
            if len(parts) < 2:
                parts = location_str.split('-')

            if len(parts) >= 2:
                brand_part = parts[0].strip()
                city_part = parts[1].strip()

                # Try to match in dataset
                for didx, disp in fl_training.iterrows():
                    disp_name = str(disp['regulator_name']).lower()
                    disp_city = str(disp['regulator_city']).lower()

                    # Check if city matches and brand is in name
                    brand_match = any(word in disp_name for word in brand_part.lower().split()[:2])
                    city_match = city_part.lower() in disp_city or disp_city in city_part.lower()

                    if brand_match and city_match:
                        matches.append({
                            'dataset_idx': didx,
                            'regulator_name': disp['regulator_name'],
                            'regulator_city': disp['regulator_city'],
                            'opening_location': location_str,
                            'opening_date': opening['opening_date'],
                            'months_operational': opening['months_operational']
                        })
                        break  # Only match once

        print(f"✅ Matched {len(matches)} FL openings to training dispensaries")
        print()

        if len(matches) > 0:
            # Show sample matches
            matches_df = pd.DataFrame(matches)
            print("Sample matches:")
            print(matches_df[['regulator_name', 'months_operational']].head(10).to_string(index=False))
            print()

        return matches

    def apply_temporal_adjustments(self, matches):
        """Apply temporal adjustments to FL dispensaries <12 months old."""
        print("="*70)
        print("APPLYING FL TEMPORAL ADJUSTMENTS")
        print("="*70)
        print()

        if len(matches) == 0:
            print("⚠️  No matches found - skipping temporal adjustments")
            print()
            return

        # Create annualization lookup
        # Maturity curve: how much of steady-state performance is reached by month X
        # Based on typical dispensary ramp-up (conservative estimates)
        maturity_curve = {
            1: 0.30, 2: 0.40, 3: 0.50,
            4: 0.60, 5: 0.70, 6: 0.75,
            7: 0.80, 8: 0.85, 9: 0.90,
            10: 0.95, 11: 0.98, 12: 1.00
        }

        print("Using maturity curve for annualization:")
        print("  Months operational → % of steady-state performance")
        for month in [3, 6, 9, 12]:
            print(f"    {month} months: {maturity_curve.get(month, 1.0)*100:.0f}%")
        print()

        # Apply adjustments
        adjusted_count = 0

        for match in matches:
            idx = match['dataset_idx']
            months_op = match['months_operational']

            # Get maturity factor (interpolate if needed)
            month_floor = int(np.floor(months_op))
            maturity_factor = maturity_curve.get(month_floor, 1.0)

            # Get current corrected visits (after Placer correction)
            current_visits = self.df.loc[idx, 'corrected_visits_step1']

            if pd.notna(current_visits) and maturity_factor < 1.0:
                # Annualize: divide by maturity factor
                annualized_visits = current_visits / maturity_factor

                self.df.loc[idx, 'corrected_visits'] = annualized_visits
                self.df.loc[idx, 'temporal_adjustment_applied'] = True
                self.df.loc[idx, 'months_operational_at_collection'] = months_op
                self.df.loc[idx, 'maturity_factor'] = maturity_factor

                adjusted_count += 1

        print(f"✅ Applied temporal adjustments to {adjusted_count} FL dispensaries")
        print()

        # For dispensaries NOT adjusted (either FL >12 months or non-FL)
        # Copy step1 to final
        not_adjusted_mask = self.df['temporal_adjustment_applied'] != True
        self.df.loc[not_adjusted_mask, 'corrected_visits'] = (
            self.df.loc[not_adjusted_mask, 'corrected_visits_step1']
        )

        # Show impact
        if adjusted_count > 0:
            adjusted_mask = self.df['temporal_adjustment_applied'] == True
            print("Impact of temporal adjustments:")
            print(f"  Mean before: {self.df.loc[adjusted_mask, 'corrected_visits_step1'].mean():,.0f}")
            print(f"  Mean after: {self.df.loc[adjusted_mask, 'corrected_visits'].mean():,.0f}")
            print(f"  Average increase: {(self.df.loc[adjusted_mask, 'corrected_visits'].mean() / self.df.loc[adjusted_mask, 'corrected_visits_step1'].mean() - 1) * 100:.1f}%")
            print()

    def save_corrected_dataset(self, output_path=None):
        """Save corrected dataset with clear column naming."""
        if output_path is None:
            output_path = 'data/processed/combined_with_competitive_features_corrected.csv'

        # Add metadata columns
        self.df['correction_placer_factor'] = self.placer_correction_factor

        # Update visits_per_sq_ft to use corrected_visits
        self.df['corrected_visits_per_sq_ft'] = self.df['corrected_visits'] / self.df['sq_ft']

        # Save
        self.df.to_csv(output_path, index=False)

        print("="*70)
        print("CORRECTED DATASET SAVED")
        print("="*70)
        print(f"Output: {output_path}")
        print()
        print("Column naming convention:")
        print("  - placer_visits: Original Placer ANNUAL estimates (UNCORRECTED)")
        print("  - corrected_visits: ANNUAL visits after Placer + temporal corrections (USE FOR MODELING)")
        print("  - corrected_visits_per_sq_ft: Efficiency metric with corrected data")
        print()
        print("⚠️  IMPORTANT: All 'visits' metrics are ANNUAL, not monthly")
        print()

        # Summary statistics
        training_mask = self.df['has_placer_data'] == True
        print("Training data summary:")
        print(f"  Dispensaries: {training_mask.sum()}")
        print(f"  Mean placer_visits: {self.df.loc[training_mask, 'placer_visits'].mean():,.0f}")
        print(f"  Mean corrected_visits: {self.df.loc[training_mask, 'corrected_visits'].mean():,.0f}")
        print(f"  Overall correction: +{(self.df.loc[training_mask, 'corrected_visits'].mean() / self.df.loc[training_mask, 'placer_visits'].mean() - 1) * 100:.1f}%")
        print()

        return output_path

    def run_full_correction(self):
        """Run complete correction workflow."""
        self.load_data()

        # Step 1: Placer Correction
        self.load_insa_actual_data()
        insa_comparison = self.match_insa_to_placer()

        if insa_comparison is None:
            print("❌ Cannot proceed without Insa data match")
            return None

        self.apply_placer_correction()

        # Step 2: FL Temporal Adjustments
        self.load_fl_openings()
        self.parse_opening_dates()
        fl_matches = self.match_openings_to_training_data()
        self.apply_temporal_adjustments(fl_matches)

        # Save
        output_path = self.save_corrected_dataset()

        print("="*70)
        print("✅ CORRECTION COMPLETE")
        print("="*70)
        print()
        print("Next steps:")
        print("1. Review corrected dataset")
        print("2. Retrain model using 'corrected_visits' as target")
        print("3. Compare R² vs baseline (v1)")
        print()

        return output_path


def main():
    """Main entry point."""
    print("\n")
    print("="*70)
    print("MULTI-STATE DISPENSARY MODEL - DATA CORRECTION")
    print("="*70)
    print()

    corrector = DataCorrector()
    output_path = corrector.run_full_correction()

    if output_path:
        print(f"✅ Success! Corrected dataset: {output_path}")
    else:
        print("❌ Correction failed - see errors above")


if __name__ == "__main__":
    main()
