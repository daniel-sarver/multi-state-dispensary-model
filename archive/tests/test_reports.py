#!/usr/bin/env python3
"""
Test script for report generation functionality.

Tests the complete report generation pipeline with sample data.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.prediction.predictor import MultiStatePredictor
from src.reporting.report_generator import ReportGenerator

def main():
    """Test report generation with sample data."""
    print("=" * 70)
    print("TESTING REPORT GENERATOR".center(70))
    print("=" * 70)

    # Initialize predictor
    print("\n🔄 Loading model...")
    predictor = MultiStatePredictor()
    model_info = predictor.get_model_info()
    print("✅ Model loaded successfully")

    # Create sample analysis results
    print("\n🔄 Creating sample analysis results...")
    sample_results = [
        {
            'rank': 1,
            'state': 'PA',
            'latitude': 40.3234711,
            'longitude': -75.6167059,
            'predicted_visits': 49750,
            'ci_lower': 0,
            'ci_upper': 110223,
            'confidence_level': 'LOW',
            'sq_ft': 2800,
            'pop_1mi': 5618,
            'pop_3mi': 30159,
            'pop_5mi': 63911,
            'pop_10mi': 169647,
            'pop_20mi': 1098208,
            'competitors_1mi': 0,
            'competitors_3mi': 0,
            'competitors_5mi': 0,
            'competitors_10mi': 3,
            'competitors_20mi': 18,
            'competition_weighted_20mi': 1.3641,
            'total_population': 5618,
            'median_age': 39.3,
            'median_household_income': 122083,
            'per_capita_income': 47298,
            'population_density': 174.1,
            'total_pop_25_plus': 4000,
            'bachelors_degree': 800,
            'masters_degree': 200,
            'professional_degree': 50,
            'doctorate_degree': 25,
            'tract_area_sqm': 4561619
        },
        {
            'rank': 2,
            'state': 'PA',
            'latitude': 40.1074,
            'longitude': -74.9515,
            'predicted_visits': 45000,
            'ci_lower': 5000,
            'ci_upper': 95000,
            'confidence_level': 'MODERATE',
            'sq_ft': 3500,
            'pop_1mi': 8000,
            'pop_3mi': 40000,
            'pop_5mi': 80000,
            'pop_10mi': 200000,
            'pop_20mi': 1200000,
            'competitors_1mi': 1,
            'competitors_3mi': 2,
            'competitors_5mi': 3,
            'competitors_10mi': 8,
            'competitors_20mi': 25,
            'competition_weighted_20mi': 2.5,
            'total_population': 8000,
            'median_age': 35.5,
            'median_household_income': 95000,
            'per_capita_income': 42000,
            'population_density': 250.0,
            'total_pop_25_plus': 5500,
            'bachelors_degree': 1000,
            'masters_degree': 300,
            'professional_degree': 75,
            'doctorate_degree': 30,
            'tract_area_sqm': 3500000
        }
    ]

    print(f"✅ Created {len(sample_results)} sample results")

    # Generate reports
    print("\n🔄 Generating comprehensive reports...")
    report_gen = ReportGenerator(model_info)

    try:
        generated_files = report_gen.generate_reports(sample_results)

        print("\n✅ Test completed successfully!")
        print("\nGenerated files:")
        for report_type, file_path in generated_files.items():
            print(f"  • {report_type.upper()}: {file_path}")

        # Show how to open HTML report
        if 'html' in generated_files:
            print(f"\nTo view the HTML report:")
            print(f"  open {generated_files['html']}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
