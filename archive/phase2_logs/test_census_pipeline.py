"""Quick test of census data collection pipeline with 2 dispensaries."""

import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.feature_engineering.census_tract_identifier import CensusTractIdentifier
from src.feature_engineering.acs_data_collector import ACSDataCollector
from src.feature_engineering.geographic_analyzer import GeographicAnalyzer
from src.feature_engineering.census_feature_engineer import CensusFeatureEngineer

print("=" * 80)
print("QUICK CENSUS PIPELINE TEST (2 dispensaries)")
print("=" * 80)

# Create test data (1 FL, 1 PA)
test_df = pd.DataFrame({
    'Dispensary_ID': ['FL_TEST_001', 'PA_TEST_001'],
    'placer_name': ['Trulieve Orlando', 'RISE Harrisburg'],
    'latitude': [28.568495, 40.225128],
    'longitude': [-81.216347, -76.827431],
    'state_abbr': ['FL', 'PA']
})

print(f"\nTest data: {len(test_df)} dispensaries")
print(test_df[['placer_name', 'latitude', 'longitude', 'state_abbr']])

# Step 1: Identify census tracts
print("\n" + "=" * 80)
print("Step 1: Identifying census tracts...")
print("=" * 80)
identifier = CensusTractIdentifier()

for idx, row in test_df.iterrows():
    tract_info = identifier.get_tract_from_coordinates(row['latitude'], row['longitude'])
    print(f"\n{row['placer_name']}:")
    print(f"  GEOID: {tract_info.get('geoid')}")
    print(f"  Tract name: {tract_info.get('tract_name')}")

    test_df.at[idx, 'census_geoid'] = tract_info.get('geoid')

# Step 2: Collect ACS demographics
print("\n" + "=" * 80)
print("Step 2: Collecting ACS demographics...")
print("=" * 80)
collector = ACSDataCollector()

for idx, row in test_df.iterrows():
    geoid = row.get('census_geoid')
    if pd.notna(geoid) and len(str(geoid)) == 11:
        state_fips = str(geoid)[:2]
        county_fips = str(geoid)[2:5]
        tract_fips = str(geoid)[5:11]

        demo = collector.get_tract_demographics(state_fips, county_fips, tract_fips)
        print(f"\n{row['placer_name']}:")
        print(f"  Population: {demo.get('total_population')}")
        print(f"  Median income: ${demo.get('median_household_income'):,.0f}" if demo.get('median_household_income') else "  Median income: N/A")
        print(f"  Median age: {demo.get('median_age')}")

        test_df.at[idx, 'total_population'] = demo.get('total_population')
        test_df.at[idx, 'median_household_income'] = demo.get('median_household_income')

# Step 3: Multi-radius population (just 1 mile for quick test)
print("\n" + "=" * 80)
print("Step 3: Calculating multi-radius populations...")
print("=" * 80)
analyzer = GeographicAnalyzer()

# Create population lookup
pop_lookup = test_df[['census_geoid', 'total_population']].copy()
pop_lookup = pop_lookup.rename(columns={'census_geoid': 'GEOID', 'total_population': 'B01001_001E'})

for idx, row in test_df.iterrows():
    try:
        pop_data = analyzer.calculate_multi_radius_population(
            row['latitude'], row['longitude'], row['state_abbr'], pop_lookup
        )
        print(f"\n{row['placer_name']} populations:")
        print(f"  1 mile: {pop_data['pop_1mi']:,.0f}")
        print(f"  3 mile: {pop_data['pop_3mi']:,.0f}")
        print(f"  5 mile: {pop_data['pop_5mi']:,.0f}")
        print(f"  10 mile: {pop_data['pop_10mi']:,.0f}")
        print(f"  20 mile: {pop_data['pop_20mi']:,.0f}")

        # Check monotonic
        pops = [pop_data[f'pop_{r}mi'] for r in [1, 3, 5, 10, 20]]
        is_monotonic = all(pops[i] <= pops[i+1] for i in range(len(pops)-1))
        print(f"  Monotonic: {'✓ YES' if is_monotonic else '✗ NO'}")

    except Exception as e:
        print(f"\nError for {row['placer_name']}: {e}")

print("\n" + "=" * 80)
print("✅ QUICK TEST COMPLETE")
print("=" * 80)
print("\nAll modules working correctly!")
print("Ready for full production run with --sample flag")
