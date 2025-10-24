#!/usr/bin/env python3
"""
Quick test script for Phase 3 CLI integration.
Tests coordinate calculator integration with known Insa Orlando location.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.feature_engineering.data_loader import MultiStateDataLoader
from src.feature_engineering.coordinate_calculator import CoordinateFeatureCalculator
from src.prediction.feature_validator import FeatureValidator
from src.prediction.predictor import MultiStatePredictor

def test_coordinate_calculation():
    """Test coordinate-based feature calculation for Insa Orlando."""
    print("=" * 70)
    print("Phase 3 CLI Integration Test".center(70))
    print("=" * 70)

    # Known Insa Orlando location
    state = 'FL'
    lat = 28.5685
    lon = -81.2163
    sq_ft = None  # Use default

    print(f"\n📍 Test Location: Insa Orlando, FL")
    print(f"  Coordinates: {lat}, {lon}")
    print(f"  Square footage: {'Default' if sq_ft is None else sq_ft}")

    # Initialize components
    print("\n🔄 Initializing data loader and calculator...")
    data_loader = MultiStateDataLoader()
    calculator = CoordinateFeatureCalculator(data_loader)
    validator = FeatureValidator()
    predictor = MultiStatePredictor()
    print("✅ Components initialized")

    # Calculate features from coordinates
    print("\n🔄 Calculating features from coordinates...")
    try:
        base_features = calculator.calculate_all_features(state, lat, lon, sq_ft)
        print("✅ Features calculated successfully")

        # Display key features
        print("\n📊 Calculated Base Features:")
        print(f"  • Square footage: {base_features['sq_ft']:,.0f}")
        print(f"  • Population (1mi): {base_features['pop_1mi']:,}")
        print(f"  • Population (3mi): {base_features['pop_3mi']:,}")
        print(f"  • Population (5mi): {base_features['pop_5mi']:,}")
        print(f"  • Population (10mi): {base_features['pop_10mi']:,}")
        print(f"  • Population (20mi): {base_features['pop_20mi']:,}")
        print(f"  • Competitors (5mi): {base_features['competitors_5mi']}")
        print(f"  • Competitors (10mi): {base_features['competitors_10mi']}")
        print(f"  • Census tract: {base_features.get('census_geoid', 'N/A')}")
        print(f"  • Median income: ${base_features['median_household_income']:,.0f}")

    except Exception as e:
        print(f"❌ Feature calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Validate and generate derived features
    print("\n🔄 Validating and generating derived features...")
    try:
        complete_features = validator.prepare_features(base_features, state)
        print(f"✅ Validation complete - {len(complete_features)} features generated")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Generate prediction
    print("\n🔄 Generating prediction...")
    try:
        result = predictor.predict_with_confidence(
            complete_features,
            confidence=0.95,
            method='normal'
        )

        print("✅ Prediction generated")
        print(f"\n🎯 Prediction Results:")
        print(f"  • Expected Annual Visits: {result['prediction']:,.0f}")
        print(f"  • 95% Confidence Interval: {result['ci_lower']:,.0f} - {result['ci_upper']:,.0f}")
        print(f"  • Prediction Range: ±{(result['ci_upper'] - result['ci_lower']) / 2:,.0f} visits")

        # Get top drivers
        top_drivers = predictor.get_top_drivers(complete_features, n=3)
        print(f"\n🔝 Top 3 Feature Drivers:")
        for idx, row in top_drivers.iterrows():
            print(f"  • {row['feature'].replace('_', ' ').title()}: {row['contribution']:+,.0f} visits")

    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED".center(70))
    print("=" * 70)

    return True

if __name__ == "__main__":
    success = test_coordinate_calculation()
    sys.exit(0 if success else 1)
