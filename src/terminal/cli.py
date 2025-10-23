#!/usr/bin/env python3
"""
Interactive Terminal Interface for Multi-State Dispensary Prediction Model

Provides user-friendly CLI for generating predictions with automatic feature
validation and generation. Supports both interactive single-site analysis and
batch processing from CSV files.

Usage:
    python3 src/terminal/cli.py
"""

import sys
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.prediction.predictor import MultiStatePredictor
from src.prediction.feature_validator import FeatureValidator


class TerminalInterface:
    """Interactive CLI for multi-state dispensary predictions."""

    def __init__(self):
        """Initialize predictor and validator."""
        print("\n🔄 Loading model...")
        try:
            self.predictor = MultiStatePredictor()
            self.validator = FeatureValidator()
            print("✅ Model loaded successfully\n")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            sys.exit(1)

    def run(self):
        """Main entry point - run interactive session."""
        self.print_header()

        while True:
            mode = self.select_mode()

            if mode == 'single':
                self.run_single_site_analysis()
            elif mode == 'batch':
                self.run_batch_analysis()
            elif mode == 'info':
                self.show_model_info()
            elif mode == 'exit':
                print("\n👋 Thanks for using the Multi-State Dispensary Model!")
                break

            print()  # Spacing between iterations

    def print_header(self):
        """Print CLI header with model information."""
        info = self.predictor.get_model_info()

        print("=" * 70)
        print("MULTI-STATE DISPENSARY PREDICTION MODEL".center(70))
        print("=" * 70)
        print(f"Model Version:    v1.0")
        print(f"Training Date:    {info['training_date'][:10]}")
        print(f"Test R²:          {info['test_r2']:.4f}")
        print(f"Cross-Val R²:     {info['cv_r2_mean']:.4f} ± {info['cv_r2_std']:.4f}")
        print(f"Improvement:      {info['improvement_over_baseline']}")
        print("=" * 70)

    def select_mode(self) -> str:
        """Let user choose operating mode."""
        print("\nSelect Mode:")
        print("  [1] Single Site Analysis (Interactive)")
        print("  [2] Batch Analysis (CSV Input)")
        print("  [3] Model Information")
        print("  [4] Exit")

        while True:
            choice = input("\n> Select mode (1-4): ").strip()

            if choice == '1':
                return 'single'
            elif choice == '2':
                return 'batch'
            elif choice == '3':
                return 'info'
            elif choice == '4':
                return 'exit'
            else:
                print("❌ Invalid choice. Please enter 1-4.")

    def run_single_site_analysis(self):
        """Interactive single-site prediction."""
        print("\n" + "=" * 70)
        print("SINGLE SITE ANALYSIS".center(70))
        print("=" * 70)

        # Get state
        state = self.prompt_state()
        if state is None:
            return

        print(f"\n📍 State: {state}")
        print("\nEnter site characteristics (23 features required)")
        print("Type 'cancel' to return to main menu\n")

        # Collect features
        base_features = self.prompt_base_features(state)
        if base_features is None:
            print("\n⚠️  Analysis cancelled")
            return

        # Validate and generate features
        print("\n🔄 Validating inputs and generating derived features...")
        try:
            complete_features = self.validator.prepare_features(
                base_features, state
            )
            print("✅ All inputs valid - 44 features generated")
        except ValueError as e:
            print(f"\n❌ Validation Error: {e}")
            return

        # Generate prediction
        print("🔄 Generating prediction with confidence intervals...")
        try:
            result = self.predictor.predict_with_confidence(
                complete_features,
                confidence=0.95,
                method='normal'
            )

            # Get top drivers
            top_drivers = self.predictor.get_top_drivers(
                complete_features, n=5
            )

            # Pretty-print results
            self.print_results(state, base_features, result, top_drivers)

        except Exception as e:
            print(f"\n❌ Prediction Error: {e}")
            return

    def run_batch_analysis(self):
        """Batch prediction from CSV file."""
        print("\n" + "=" * 70)
        print("BATCH ANALYSIS".center(70))
        print("=" * 70)

        print("\nBatch Mode Requirements:")
        print("  - CSV file with columns for all 23 base features")
        print("  - Must include 'state' column with 'FL' or 'PA'")
        print("  - One row per site to analyze")

        # Get file path
        csv_path = input("\n> Enter CSV file path (or 'cancel'): ").strip()
        if csv_path.lower() == 'cancel':
            return

        # Load CSV
        try:
            df = pd.read_csv(csv_path)
            print(f"✅ Loaded {len(df)} sites from {csv_path}")
        except FileNotFoundError:
            print(f"❌ File not found: {csv_path}")
            return
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return

        # Validate required columns
        required_cols = self.validator.get_required_base_features() + ['state']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"❌ Missing required columns: {', '.join(missing_cols)}")
            return

        # Process each site
        print(f"\n🔄 Processing {len(df)} sites...")
        results = []

        for idx, row in df.iterrows():
            try:
                # Extract base features
                base_features = {
                    col: row[col]
                    for col in self.validator.get_required_base_features()
                }
                state = str(row['state']).upper()

                # Validate and generate
                complete_features = self.validator.prepare_features(
                    base_features, state
                )

                # Predict
                result = self.predictor.predict_with_confidence(
                    complete_features,
                    confidence=0.95,
                    method='normal'
                )

                # Store result
                result_row = {
                    'site_id': idx + 1,
                    'state': state,
                    'sq_ft': base_features['sq_ft'],
                    'pop_5mi': base_features['pop_5mi'],
                    'competitors_5mi': base_features['competitors_5mi'],
                    'predicted_visits': result['prediction'],
                    'ci_lower': result['ci_lower'],
                    'ci_upper': result['ci_upper'],
                    'ci_range': result['ci_upper'] - result['ci_lower'],
                    'confidence_level': 'HIGH' if result['ci_upper'] - result['ci_lower'] < 50000 else 'MODERATE' if result['ci_upper'] - result['ci_lower'] < 100000 else 'LOW'
                }
                results.append(result_row)

                print(f"  ✅ Site {idx + 1}/{len(df)} processed")

            except Exception as e:
                print(f"  ❌ Site {idx + 1} failed: {e}")
                results.append({
                    'site_id': idx + 1,
                    'state': row.get('state', 'UNKNOWN'),
                    'error': str(e)
                })

        # Save results
        results_df = pd.DataFrame(results)
        output_path = csv_path.replace('.csv', '_predictions.csv')
        results_df.to_csv(output_path, index=False)

        print(f"\n✅ Batch processing complete!")
        print(f"📊 Results saved to: {output_path}")

        # Show summary
        successful = len([r for r in results if 'error' not in r])
        print(f"\nSummary:")
        print(f"  Total Sites:     {len(results)}")
        print(f"  Successful:      {successful}")
        print(f"  Failed:          {len(results) - successful}")

        if successful > 0:
            avg_pred = results_df[results_df['predicted_visits'].notna()]['predicted_visits'].mean()
            print(f"  Avg Prediction:  {avg_pred:,.0f} visits/month")

    def show_model_info(self):
        """Display detailed model information."""
        info = self.predictor.get_model_info()

        print("\n" + "=" * 70)
        print("MODEL INFORMATION".center(70))
        print("=" * 70)

        print("\n📊 Overall Performance:")
        print(f"  Test R²:               {info['test_r2']:.4f}")
        print(f"  Test RMSE:             {info['test_rmse']:,.0f} visits/month")
        print(f"  Cross-Val R²:          {info['cv_r2_mean']:.4f} ± {info['cv_r2_std']:.4f}")
        print(f"  Improvement:           {info['improvement_over_baseline']}")

        print("\n🏛️  Florida Performance:")
        print(f"  Test R²:               {info['fl_r2']:.4f}")
        print(f"  Test RMSE:             {info['fl_rmse']:,.0f} visits/month")

        print("\n🏛️  Pennsylvania Performance:")
        print(f"  Test R²:               {info['pa_r2']:.4f}")
        print(f"  Test RMSE:             {info['pa_rmse']:,.0f} visits/month")

        print("\n🔧 Model Configuration:")
        print(f"  Model Type:            Ridge Regression")
        print(f"  Features:              {info['n_features']}")
        print(f"  Alpha (Regularization): {info['alpha']}")
        print(f"  Training Date:         {info['training_date']}")

        print("\n💡 Interpretation:")
        print("  - R² = 0.19 means the model explains ~19% of visit variance")
        print("  - 81% remains unexplained (product quality, marketing, staff, etc.)")
        print("  - Use for directional guidance, not precise forecasts")
        print("  - Always consider confidence intervals for decision-making")

    def prompt_state(self) -> Optional[str]:
        """Prompt user to select FL or PA."""
        print("\nState Selection:")
        print("  [1] Florida")
        print("  [2] Pennsylvania")

        while True:
            choice = input("\n> Select state (1-2, or 'cancel'): ").strip().lower()

            if choice == 'cancel':
                return None
            elif choice == '1':
                return 'FL'
            elif choice == '2':
                return 'PA'
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 'cancel'.")

    def prompt_base_features(self, state: str) -> Optional[Dict[str, Any]]:
        """Prompt for all 23 base features with validation."""
        features = {}

        # Get feature ranges for validation feedback
        ranges = self.validator.get_feature_ranges()

        # 1. Square Footage
        print("\n--- Dispensary Characteristics ---")
        sq_ft = self._prompt_float(
            "Square footage",
            ranges.get('sq_ft'),
            example="4587"
        )
        if sq_ft is None:
            return None
        features['sq_ft'] = sq_ft

        # 2-6. Multi-Radius Populations
        print("\n--- Multi-Radius Population ---")
        for radius in [1, 3, 5, 10, 20]:
            pop = self._prompt_float(
                f"Population ({radius} mile{'s' if radius > 1 else ''})",
                ranges.get(f'pop_{radius}mi'),
                example="71106" if radius == 5 else None
            )
            if pop is None:
                return None
            features[f'pop_{radius}mi'] = pop

        # 7-11. Competition Counts
        print("\n--- Competition Analysis ---")
        for radius in [1, 3, 5, 10, 20]:
            comp = self._prompt_int(
                f"Competitors ({radius} mile{'s' if radius > 1 else ''})",
                example="3" if radius == 5 else None
            )
            if comp is None:
                return None
            features[f'competitors_{radius}mi'] = comp

        # 12. Distance-weighted competition
        comp_weighted = self._prompt_float(
            "Distance-weighted competition (20mi)",
            ranges.get('competition_weighted_20mi'),
            example="1.78",
            help_text="Pre-computed from distance matrix (sum of 1/distance for each competitor)"
        )
        if comp_weighted is None:
            return None
        features['competition_weighted_20mi'] = comp_weighted

        # 13-23. Census Demographics
        print("\n--- Census Demographics ---")

        demo_fields = [
            ('total_population', 'Total population', '4062'),
            ('median_age', 'Median age', '29.1'),
            ('median_household_income', 'Median household income ($)', '76458'),
            ('per_capita_income', 'Per capita income ($)', '37439'),
            ('total_pop_25_plus', 'Total population 25+', '2369'),
            ('bachelors_degree', "Bachelor's degrees", '424'),
            ('masters_degree', "Master's degrees", '125'),
            ('professional_degree', 'Professional degrees', '0'),
            ('doctorate_degree', 'Doctorate degrees', '18'),
            ('population_density', 'Population density (per sq mi)', '890.55'),
            ('tract_area_sqm', 'Tract area (sq meters)', '4561619.35'),
        ]

        for field_name, prompt_text, example in demo_fields:
            value = self._prompt_float(
                prompt_text,
                ranges.get(field_name),
                example=example
            )
            if value is None:
                return None
            features[field_name] = value

        return features

    def _prompt_float(
        self,
        prompt: str,
        range_info: Optional[Dict] = None,
        example: Optional[str] = None,
        help_text: Optional[str] = None
    ) -> Optional[float]:
        """Prompt for a float value with validation."""
        prompt_text = f"> {prompt}: "

        # Add example if provided
        if example:
            prompt_text = f"> {prompt} (e.g., {example}): "

        while True:
            response = input(prompt_text).strip().lower()

            if response == 'cancel':
                return None

            try:
                value = float(response)

                # Provide feedback based on range
                if range_info:
                    min_val = range_info['min']
                    max_val = range_info['max']

                    if value < min_val or value > max_val:
                        print(f"  ⚠️  Warning: Value outside training range ({min_val:,.0f} - {max_val:,.0f})")
                        print(f"  ℹ️  Training mean: {range_info['mean']:,.0f}")

                return value

            except ValueError:
                print(f"  ❌ Invalid input. Please enter a number or 'cancel'.")
                if help_text:
                    print(f"  ℹ️  {help_text}")

    def _prompt_int(
        self,
        prompt: str,
        example: Optional[str] = None
    ) -> Optional[int]:
        """Prompt for an integer value."""
        prompt_text = f"> {prompt}: "

        if example:
            prompt_text = f"> {prompt} (e.g., {example}): "

        while True:
            response = input(prompt_text).strip().lower()

            if response == 'cancel':
                return None

            try:
                return int(float(response))  # Allow decimal input, convert to int
            except ValueError:
                print(f"  ❌ Invalid input. Please enter a whole number or 'cancel'.")

    def print_results(
        self,
        state: str,
        base_features: Dict[str, Any],
        result: Dict[str, Any],
        top_drivers: pd.DataFrame
    ):
        """Pretty-print prediction results (PA model style)."""
        print("\n" + "=" * 70)
        print("PREDICTION RESULTS".center(70))
        print("=" * 70)

        # Site Summary
        print("\n📍 Site Summary:")
        print(f"  State:                     {state}")
        print(f"  Square Footage:            {base_features['sq_ft']:,.0f} sq ft")
        print(f"  Population (5mi):          {base_features['pop_5mi']:,.0f}")
        print(f"  Competitors (5mi):         {base_features['competitors_5mi']:.0f}")

        # Calculate saturation for display
        saturation = (base_features['competitors_5mi'] / base_features['pop_5mi'] * 100000) if base_features['pop_5mi'] > 0 else 0
        print(f"  Market Saturation:         {saturation:.2f} per 100k")

        # Prediction
        print("\n🎯 Prediction:")
        print(f"  Expected Monthly Visits:   {result['prediction']:,.0f}")
        print(f"  95% Confidence Interval:   {result['ci_lower']:,.0f} - {result['ci_upper']:,.0f}")

        # Confidence level assessment
        ci_range = result['ci_upper'] - result['ci_lower']
        if ci_range < 50000:
            conf_level = "HIGH"
        elif ci_range < 100000:
            conf_level = "MODERATE"
        else:
            conf_level = "LOW"
        print(f"  Confidence Level:          {conf_level}")

        # Uncertainty
        print("\n📊 Uncertainty:")
        print(f"  Method:                    {result['method'].replace('_', ' ').title()}")
        print(f"  State RMSE:                {result['rmse_used']:,.0f} ({state}-specific)")
        print(f"  Prediction Range:          ±{ci_range / 2:,.0f} visits")

        # Top Feature Drivers
        print("\n🔝 Top Feature Drivers:")
        for idx, row in top_drivers.iterrows():
            feature = row['feature']
            impact = row['contribution']

            # Format feature name
            feature_display = feature.replace('_', ' ').title()

            # Direction indicator
            if impact > 0:
                direction = "✅"
                strength = "strong positive" if abs(impact) > 5000 else "moderate positive" if abs(impact) > 1000 else "weak positive"
            else:
                direction = "⚠️ "
                strength = "strong negative" if abs(impact) > 5000 else "moderate negative" if abs(impact) > 1000 else "weak negative"

            print(f"  {direction} {feature_display:30s} {impact:+8,.0f} visits ({strength})")

        # Model Performance
        info = self.predictor.get_model_info()
        print("\n📈 Model Performance:")
        print(f"  Test R²:                   {info['test_r2']:.3f}")
        print(f"  Cross-Validation R²:       {info['cv_r2_mean']:.3f} ± {info['cv_r2_std']:.3f}")
        print(f"  Improvement over Baseline: {info['improvement_over_baseline']}")

        # Interpretation
        print("\n💡 Interpretation:")
        if conf_level == "LOW":
            print(f"  This site shows predicted performance of {result['prediction']:,.0f} visits/month")
            print(f"  with HIGH uncertainty. The wide confidence interval ({ci_range:,.0f} range)")
            print(f"  reflects the model's limited explanatory power (R² = {info['test_r2']:.2f}).")
            print(f"  Consider this prediction as DIRECTIONAL GUIDANCE rather than a")
            print(f"  precise forecast.")
        elif conf_level == "MODERATE":
            print(f"  This site shows predicted performance of {result['prediction']:,.0f} visits/month")
            print(f"  with MODERATE uncertainty. The confidence interval ({ci_range:,.0f} range)")
            print(f"  reflects typical model uncertainty (R² = {info['test_r2']:.2f}).")
            print(f"  Use as guidance for site comparison and ranking.")
        else:
            print(f"  This site shows predicted performance of {result['prediction']:,.0f} visits/month")
            print(f"  with relatively LOW uncertainty. The narrow confidence interval")
            print(f"  ({ci_range:,.0f} range) suggests higher confidence in this prediction.")

        # Key factors
        if len(top_drivers) > 0:
            top_row = top_drivers.iloc[0]
            feature_name = top_row['feature'].replace('_', ' ').title()
            contribution = top_row['contribution']
            print(f"\n  Key factor: {feature_name} is the")
            print(f"  strongest driver ({contribution:+,.0f} visits impact).")

        print("\n" + "=" * 70)


def main():
    """Entry point for CLI."""
    try:
        cli = TerminalInterface()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
