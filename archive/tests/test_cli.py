#!/usr/bin/env python3
"""
Quick test of the terminal interface to verify it works correctly.
Tests model info display and predictor integration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.terminal.cli import TerminalInterface

def test_cli_initialization():
    """Test that CLI initializes correctly."""
    print("=" * 70)
    print("Testing CLI Initialization".center(70))
    print("=" * 70)

    try:
        cli = TerminalInterface()
        print("\n✅ CLI initialized successfully")
        return cli
    except Exception as e:
        print(f"\n❌ CLI initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_model_info(cli):
    """Test model info display."""
    print("\n" + "=" * 70)
    print("Testing Model Info Display".center(70))
    print("=" * 70)

    try:
        cli.show_model_info()
        print("\n✅ Model info displayed successfully")
    except Exception as e:
        print(f"\n❌ Model info display failed: {e}")
        import traceback
        traceback.print_exc()

def test_prediction_with_known_features(cli):
    """Test prediction with a known set of features."""
    print("\n" + "=" * 70)
    print("Testing Prediction with Known Features".center(70))
    print("=" * 70)

    # Use example from training data (FL dispensary)
    base_features = {
        'sq_ft': 4587,
        'pop_1mi': 5950,
        'pop_3mi': 52821,
        'pop_5mi': 71106,
        'pop_10mi': 176028,
        'pop_20mi': 563096,
        'competitors_1mi': 0,
        'competitors_3mi': 2,
        'competitors_5mi': 3,
        'competitors_10mi': 5,
        'competitors_20mi': 13,
        'competition_weighted_20mi': 1.78,
        'total_population': 4062,
        'median_age': 29.1,
        'median_household_income': 76458,
        'per_capita_income': 37439,
        'total_pop_25_plus': 2369,
        'bachelors_degree': 424,
        'masters_degree': 125,
        'professional_degree': 0,
        'doctorate_degree': 18,
        'population_density': 890.55,
        'tract_area_sqm': 4561619.35
    }
    state = 'FL'

    try:
        # Validate and generate features
        complete_features = cli.validator.prepare_features(base_features, state)
        print(f"✅ Features validated - {len(complete_features)} features generated")

        # Generate prediction
        result = cli.predictor.predict_with_confidence(
            complete_features,
            confidence=0.95,
            method='normal'
        )

        # Get top drivers
        top_drivers = cli.predictor.get_top_drivers(complete_features, n=5)

        # Print results
        cli.print_results(state, base_features, result, top_drivers)

        print("\n✅ Prediction completed successfully")

    except Exception as e:
        print(f"\n❌ Prediction failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("TERMINAL INTERFACE TEST SUITE".center(70))
    print("=" * 70)

    # Test 1: Initialization
    cli = test_cli_initialization()
    if cli is None:
        print("\n❌ Cannot proceed with tests - initialization failed")
        sys.exit(1)

    # Test 2: Model info
    test_model_info(cli)

    # Test 3: Prediction
    test_prediction_with_known_features(cli)

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED".center(70))
    print("=" * 70)
    print("\nTerminal interface is ready for interactive use!")
    print("Run: python3 src/terminal/cli.py")

if __name__ == "__main__":
    main()
