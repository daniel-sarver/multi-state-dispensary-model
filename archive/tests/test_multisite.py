#!/usr/bin/env python3
"""
Test script for multi-site analysis workflow.

Demonstrates the new multi-site capability with sample PA coordinates.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.prediction.predictor import MultiStatePredictor
from src.prediction.feature_validator import FeatureValidator
from src.feature_engineering.data_loader import MultiStateDataLoader
from src.feature_engineering.coordinate_calculator import CoordinateFeatureCalculator
from src.reporting.report_generator import ReportGenerator

def test_multisite_workflow():
    """Test the multi-site analysis workflow."""
    print("=" * 70)
    print("TESTING MULTI-SITE ANALYSIS WORKFLOW".center(70))
    print("=" * 70)

    # Sample PA sites for testing
    test_sites = [
        {
            'name': 'Site 1 - Pottstown Area',
            'state': 'PA',
            'latitude': 40.3234711,
            'longitude': -75.6167059,
            'sq_ft': 2800
        },
        {
            'name': 'Site 2 - Bensalem Area',
            'state': 'PA',
            'latitude': 40.1074,
            'longitude': -74.9515,
            'sq_ft': 3500
        },
        {
            'name': 'Site 3 - Sunbury Area',
            'state': 'PA',
            'latitude': 40.8707,
            'longitude': -76.7864,
            'sq_ft': 4000
        }
    ]

    # Initialize components
    print("\n🔄 Initializing model and data sources...")
    predictor = MultiStatePredictor()
    validator = FeatureValidator()
    data_loader = MultiStateDataLoader()
    calculator = CoordinateFeatureCalculator(data_loader)
    print("✅ Components initialized")

    # Analyze each site
    all_results = []
    print(f"\n🔄 Analyzing {len(test_sites)} sites...")
    print("-" * 70)

    for i, site in enumerate(test_sites, 1):
        print(f"\n{'='*70}")
        print(f"SITE {i} - {site['name']}".center(70))
        print(f"{'='*70}")

        print(f"  State: {site['state']}")
        print(f"  Coordinates: {site['latitude']}, {site['longitude']}")
        print(f"  Square Footage: {site['sq_ft']:,} sq ft")

        try:
            # Calculate features
            print("\n  🔄 Calculating features...")
            base_features = calculator.calculate_all_features(
                site['state'],
                site['latitude'],
                site['longitude'],
                site['sq_ft']
            )

            print(f"  ✅ Features calculated")
            print(f"     • Population (5mi): {base_features['pop_5mi']:,}")
            print(f"     • Competitors (5mi): {base_features['competitors_5mi']}")

            # Validate features
            complete_features = validator.prepare_features(
                base_features, site['state']
            )

            # Generate prediction
            result = predictor.predict_with_confidence(
                complete_features,
                confidence=0.95,
                method='normal'
            )

            # Prepare result dict
            ci_range = result['ci_upper'] - result['ci_lower']
            if ci_range < 50000:
                conf_level = "HIGH"
            elif ci_range < 100000:
                conf_level = "MODERATE"
            else:
                conf_level = "LOW"

            analysis_result = {
                'site_number': i,
                'site_name': site['name'],
                'state': site['state'],
                'latitude': site['latitude'],
                'longitude': site['longitude'],
                'predicted_visits': result['prediction'],
                'ci_lower': result['ci_lower'],
                'ci_upper': result['ci_upper'],
                'confidence_level': conf_level,
                **base_features
            }

            all_results.append(analysis_result)

            print(f"\n  ✅ Site {i} Analysis Complete")
            print(f"     Predicted Annual Visits: {result['prediction']:,.0f}")
            print(f"     95% CI: {result['ci_lower']:,.0f} - {result['ci_upper']:,.0f}")
            print(f"     Confidence: {conf_level}")

        except Exception as e:
            print(f"\n  ❌ Error analyzing site {i}: {e}")
            import traceback
            traceback.print_exc()

    # Display comparison summary
    print("\n" + "=" * 70)
    print("MULTI-SITE COMPARISON SUMMARY".center(70))
    print("=" * 70)

    # Sort by predicted visits
    sorted_results = sorted(
        all_results,
        key=lambda x: x['predicted_visits'],
        reverse=True
    )

    # Print comparison table
    print(f"\n{'Rank':<6} {'Site':<6} {'State':<7} {'Predicted Visits':<20} {'Confidence':<12}")
    print("-" * 70)

    for rank, result in enumerate(sorted_results, 1):
        result['rank'] = rank
        site_num = result['site_number']
        visits_str = f"{result['predicted_visits']:,.0f}"
        conf = result['confidence_level']
        print(f"#{rank:<5} Site {site_num:<2} {result['state']:<7} {visits_str:<20} {conf:<12}")

    # Print statistics
    print("\n" + "-" * 70)
    print("Summary Statistics:")
    avg_visits = sum(r['predicted_visits'] for r in all_results) / len(all_results)
    max_visits = max(r['predicted_visits'] for r in all_results)
    min_visits = min(r['predicted_visits'] for r in all_results)

    print(f"  Total Sites Analyzed:  {len(all_results)}")
    print(f"  Average Prediction:    {avg_visits:,.0f} visits/year")
    print(f"  Range:                 {min_visits:,.0f} - {max_visits:,.0f} visits/year")
    print(f"  Spread:                {max_visits - min_visits:,.0f} visits/year")

    # Show best site
    best_site = sorted_results[0]
    print(f"\n🏆 Best Performing Site:")
    print(f"  Site {best_site['site_number']} - {best_site['site_name']}")
    print(f"  Predicted Visits: {best_site['predicted_visits']:,.0f}")
    print(f"  Population (5mi): {best_site['pop_5mi']:,.0f}")
    print(f"  Competitors (5mi): {best_site['competitors_5mi']}")

    # Generate reports
    print("\n" + "=" * 70)
    print("🔄 Generating comprehensive reports...")
    report_gen = ReportGenerator(predictor.get_model_info())
    generated_files = report_gen.generate_reports(sorted_results)

    print(f"\n✅ Test completed successfully!")
    print(f"\n📊 Reports generated:")
    for report_type, file_path in generated_files.items():
        print(f"  • {report_type.upper()}: {file_path}")

    if 'html' in generated_files:
        print(f"\nTo view the HTML report:")
        print(f"  open {generated_files['html']}")

    return True

if __name__ == "__main__":
    try:
        success = test_multisite_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
