"""
Placer Visit Correction Using Insa Actual Data

Purpose: Calibrate Placer visit estimates using actual visit counts from Insa stores
Approach: Calculate correction factors and apply to training data before modeling
Output: Corrected dataset and comparison analysis

Author: Claude Code
Date: October 24, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path


class PlacerCorrector:
    """Correct Placer visit estimates using actual Insa store data."""

    def __init__(self,
                 data_path='data/processed/combined_with_competitive_features.csv',
                 insa_actual_path=None):
        """
        Initialize Placer corrector.

        Parameters:
        -----------
        data_path : str
            Path to combined dataset with Placer visits
        insa_actual_path : str, optional
            Path to CSV with actual Insa visit counts
            Expected columns: store_name, city, actual_monthly_visits
        """
        self.data_path = data_path
        self.insa_actual_path = insa_actual_path
        self.df = None
        self.insa_placer = None
        self.insa_actual = None
        self.correction_factor = None

    def load_data(self):
        """Load combined dataset."""
        print("Loading combined dataset...")
        self.df = pd.read_csv(self.data_path)
        print(f"  Total dispensaries: {len(self.df)}")
        print(f"  Training dispensaries: {self.df['has_placer_data'].sum()}")
        print()

    def identify_insa_stores(self):
        """Find Insa stores in dataset."""
        print("Identifying Insa stores in Placer data...")

        # Find stores with 'insa' in the name (case-insensitive)
        insa_mask = (
            self.df['regulator_name'].str.contains('insa', case=False, na=False) |
            self.df['placer_name'].str.contains('insa', case=False, na=False)
        )

        self.insa_placer = self.df[insa_mask & (self.df['has_placer_data'] == True)].copy()

        print(f"  Insa stores with Placer data: {len(self.insa_placer)}")

        if len(self.insa_placer) > 0:
            print()
            print("  Insa stores found:")
            cols = ['regulator_name', 'regulator_city', 'visits', 'sq_ft']
            print(self.insa_placer[cols].to_string(index=False))

        print()
        return self.insa_placer

    def load_insa_actual_data(self, insa_actual_dict=None):
        """
        Load actual Insa visit data.

        Parameters:
        -----------
        insa_actual_dict : dict, optional
            Dictionary mapping city names to actual monthly visits
            Example: {'Hudson': 65000, 'Orlando': 58000, ...}
        """
        if insa_actual_dict is not None:
            # Use provided dictionary
            self.insa_actual = pd.DataFrame([
                {'city': city, 'actual_visits': visits}
                for city, visits in insa_actual_dict.items()
            ])
        elif self.insa_actual_path is not None:
            # Load from CSV file
            self.insa_actual = pd.read_csv(self.insa_actual_path)
        else:
            print("⚠️  No Insa actual data provided")
            print("   Please provide either:")
            print("     1. insa_actual_dict parameter")
            print("     2. CSV file path at initialization")
            return None

        print("Insa actual visit data loaded:")
        print(self.insa_actual.to_string(index=False))
        print()
        return self.insa_actual

    def calculate_correction_factors(self):
        """Calculate Placer-to-actual correction factors."""
        if self.insa_actual is None:
            print("⚠️  Cannot calculate correction factors - no actual data loaded")
            return None

        print("="*70)
        print("PLACER CORRECTION FACTOR CALCULATION")
        print("="*70)
        print()

        # Merge Placer and actual data by city
        merged = self.insa_placer.merge(
            self.insa_actual,
            left_on='regulator_city',
            right_on='city',
            how='inner'
        )

        if len(merged) == 0:
            print("⚠️  No matches found between Placer and actual data")
            print("   Check that city names match exactly")
            return None

        # Calculate individual correction factors
        merged['placer_visits'] = merged['visits']
        merged['correction_factor'] = merged['actual_visits'] / merged['placer_visits']
        merged['difference'] = merged['actual_visits'] - merged['placer_visits']
        merged['pct_difference'] = (merged['difference'] / merged['placer_visits']) * 100

        print(f"Matched {len(merged)} Insa stores:")
        print()

        cols = ['regulator_city', 'placer_visits', 'actual_visits',
                'difference', 'pct_difference', 'correction_factor']
        print(merged[cols].to_string(index=False))
        print()

        # Calculate overall correction factor
        simple_avg = merged['correction_factor'].mean()
        weighted_avg = (
            merged['actual_visits'].sum() / merged['placer_visits'].sum()
        )
        median_factor = merged['correction_factor'].median()

        print("="*70)
        print("CORRECTION FACTOR SUMMARY")
        print("="*70)
        print(f"  Simple average: {simple_avg:.4f}")
        print(f"  Weighted average: {weighted_avg:.4f}")
        print(f"  Median: {median_factor:.4f}")
        print()
        print(f"  Interpretation:")
        if weighted_avg > 1.0:
            print(f"    Placer UNDERESTIMATES by {(weighted_avg - 1) * 100:.1f}%")
        else:
            print(f"    Placer OVERESTIMATES by {(1 - weighted_avg) * 100:.1f}%")
        print()

        # Use weighted average as primary correction factor
        self.correction_factor = weighted_avg

        return merged

    def apply_correction(self, method='simple', custom_factor=None):
        """
        Apply correction factor to all training data.

        Parameters:
        -----------
        method : str
            'simple' - Apply single correction factor to all stores
            'state_specific' - Apply different factors for FL vs PA
            'size_adjusted' - Adjust by store size (visits/sq_ft)
        custom_factor : float, optional
            Override calculated factor with custom value
        """
        if custom_factor is not None:
            correction_factor = custom_factor
        elif self.correction_factor is not None:
            correction_factor = self.correction_factor
        else:
            print("⚠️  No correction factor available")
            return None

        print("="*70)
        print(f"APPLYING CORRECTION (method={method})")
        print("="*70)
        print()

        # Create corrected dataset
        corrected_df = self.df.copy()
        training_mask = corrected_df['has_placer_data'] == True

        if method == 'simple':
            # Apply single factor to all stores
            corrected_df.loc[training_mask, 'visits_original'] = corrected_df.loc[training_mask, 'visits']
            corrected_df.loc[training_mask, 'visits'] = (
                corrected_df.loc[training_mask, 'visits'] * correction_factor
            )
            print(f"  Applied correction factor: {correction_factor:.4f}")
            print(f"  Stores corrected: {training_mask.sum()}")

        elif method == 'state_specific':
            # Calculate state-specific factors if we have Insa data for both states
            # (Currently all Insa stores are FL, so this would use same factor)
            print("  ⚠️  State-specific correction requires Insa stores in both states")
            print("  Using simple correction for now")
            corrected_df.loc[training_mask, 'visits_original'] = corrected_df.loc[training_mask, 'visits']
            corrected_df.loc[training_mask, 'visits'] = (
                corrected_df.loc[training_mask, 'visits'] * correction_factor
            )

        # Update visits_per_sq_ft
        corrected_df['visits_per_sq_ft'] = (
            corrected_df['visits'] / corrected_df['sq_ft']
        )

        print()
        print("  Before correction:")
        print(f"    Mean visits: {self.df.loc[training_mask, 'visits'].mean():,.0f}")
        print(f"    Median visits: {self.df.loc[training_mask, 'visits'].median():,.0f}")
        print()
        print("  After correction:")
        print(f"    Mean visits: {corrected_df.loc[training_mask, 'visits'].mean():,.0f}")
        print(f"    Median visits: {corrected_df.loc[training_mask, 'visits'].median():,.0f}")
        print()

        return corrected_df

    def save_corrected_dataset(self, corrected_df, output_path=None):
        """Save corrected dataset to CSV."""
        if output_path is None:
            output_path = 'data/processed/combined_with_competitive_features_placer_corrected.csv'

        corrected_df.to_csv(output_path, index=False)
        print(f"✅ Corrected dataset saved to: {output_path}")
        print()

        return output_path

    def run_full_correction(self, insa_actual_dict=None):
        """Run complete Placer correction workflow."""
        self.load_data()
        self.identify_insa_stores()

        if insa_actual_dict is None:
            print()
            print("="*70)
            print("INSA ACTUAL DATA REQUIRED")
            print("="*70)
            print()
            print("To proceed, Daniel needs to provide actual monthly visit counts for:")
            print()

            for idx, row in self.insa_placer.iterrows():
                print(f"  - Insa {row['regulator_city']} (Placer: {row['visits']:,.0f} visits/month)")

            print()
            print("Example usage:")
            print("""
            insa_actual = {
                'Hudson': 65000,      # Actual monthly visits
                'Orlando': 58000,     # If multiple Orlando stores, provide separately
                'Largo': 51000,
                'Jacksonville': 42000,
                'Summerfield': 38000,
                'Tampa': 35000,
                'Tallahassee': 28000
            }

            corrector = PlacerCorrector()
            corrector.run_full_correction(insa_actual_dict=insa_actual)
            """)
            return None

        # Load actual data
        self.load_insa_actual_data(insa_actual_dict)

        # Calculate correction factors
        comparison = self.calculate_correction_factors()

        if comparison is None:
            return None

        # Apply correction
        corrected_df = self.apply_correction(method='simple')

        if corrected_df is not None:
            # Save corrected dataset
            output_path = self.save_corrected_dataset(corrected_df)

            print("="*70)
            print("NEXT STEPS")
            print("="*70)
            print()
            print("1. Review correction factor reasonableness")
            print("2. Retrain model using corrected dataset:")
            print(f"     python3 src/modeling/train_multi_state_model.py --data {output_path}")
            print("3. Compare R² vs baseline (v1)")
            print("4. If improved, update production model to v2")
            print()

            return {
                'corrected_df': corrected_df,
                'correction_factor': self.correction_factor,
                'comparison': comparison,
                'output_path': output_path
            }

        return None


def main():
    """Main entry point for Placer correction."""
    print("\n")
    print("="*70)
    print("PLACER VISIT CORRECTION TOOL")
    print("="*70)
    print()

    # Initialize corrector
    corrector = PlacerCorrector()

    # Example usage (requires actual data)
    print("EXAMPLE: Running with placeholder data")
    print("(Replace with actual Insa visit counts)")
    print()

    # Placeholder - to be replaced with actual data
    insa_actual_example = {
        'Hudson': 68000,      # PLACEHOLDER - need actual monthly visits
        'Orlando': 56000,     # PLACEHOLDER - need actual monthly visits
        'Largo': 52000,       # PLACEHOLDER - need actual monthly visits
        'Jacksonville': 41000,  # PLACEHOLDER - need actual monthly visits
        'Summerfield': 36000,   # PLACEHOLDER - need actual monthly visits
        'Tampa': 33000,         # PLACEHOLDER - need actual monthly visits
        'Tallahassee': 27000    # PLACEHOLDER - need actual monthly visits
    }

    # Run correction (will prompt for actual data if not provided)
    # results = corrector.run_full_correction(insa_actual_dict=insa_actual_example)
    results = corrector.run_full_correction()  # Prompts for data


if __name__ == "__main__":
    main()
