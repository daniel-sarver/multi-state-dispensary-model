# CLI Automation Implementation Plan
## Coordinate-Based Input with Automatic Feature Calculation

**Date**: October 24, 2025
**Status**: Planning Phase
**Priority**: High - Critical UX Improvement

---

## Executive Summary

Currently, the Multi-State Dispensary Model CLI requires users to manually input **23 base features** (population at 5 radii, competitors at 5 radii, census demographics, etc.). This is impractical for real-world use.

**Goal**: Transform CLI to accept **coordinates only** and automatically calculate all required features, matching the successful PA Dispensary Model pattern.

---

## Problem Statement

### Current User Experience (❌ Broken)
```
User inputs:
1. State (FL or PA)
2. Square footage
3. Population at 1mi, 3mi, 5mi, 10mi, 20mi (5 inputs)
4. Competitors at 1mi, 3mi, 5mi, 10mi, 20mi (5 inputs)
5. Distance-weighted competition score
6. Total population, median age, income, education (11 census inputs)

Total: 23 manual inputs per site
```

**Issue**: User doesn't have this data. It must be calculated programmatically.

### Target User Experience (✅ Fixed)
```
User inputs:
1. State (FL or PA)
2. Address (optional, for display)
3. Latitude, Longitude
4. Square footage (optional, model default available)

System automatically calculates:
- Population within 1, 3, 5, 10, 20 mile radii
- Competitors within same radii
- Distance-weighted competition scores
- Census tract demographics (age, income, education, density)
- All derived features (21 auto-generated features)

Total: 3-4 inputs per site
```

---

## Architecture Analysis

### PA Dispensary Model Pattern (✅ Proven)

**Key Components**:

1. **Census Data Integration** (`pa-dispensary-model/src/data_processing/census_data_consolidation_specialized.py`)
   - Pre-loaded 3,446 PA census tracts with coordinates
   - Spatial matching: site coordinates → nearest census tract
   - Auto-extract demographics for any PA location

2. **Competition Calculator** (Embedded in `update_model_banded_v3_1.py`)
   ```python
   def calculate_competitors_within_radius(self, target_coords, radius_miles):
       """Calculate competitors within specified radius."""
       competitor_count = 0
       for _, dispensary in self.pa_dispensaries.iterrows():
           distance_miles = geodesic(target_coords, disp_coords).miles
           if distance_miles <= radius_miles and distance_miles > 0.1:
               competitor_count += 1
       return competitor_count
   ```
   - Pre-loaded 192 PA dispensaries with coordinates
   - Calculates competitors at any radius on-demand
   - Uses geodesic distance (Haversine formula)

3. **Population Calculator** (Same file)
   ```python
   def calculate_population_within_radius(self, target_coords, radius_miles):
       """Calculate population within specified radius."""
       total_population = 0
       for _, tract in self.census_data.iterrows():
           distance_miles = geodesic(target_coords, tract_coords).miles
           if distance_miles <= radius_miles:
               total_population += tract['TOTAL_POPULATION']
       return total_population
   ```
   - Sums census tract populations within radius
   - Automatic multi-radius calculation (1, 3, 5, 10, 20mi)

4. **Traffic Calculator** (`real_traffic_calculator.py`)
   - **CRITICAL SAFEGUARD**: Returns explicit error if no data found
   - NO fallbacks, NO estimates without approval
   - Clear error messages halt execution

**Key Success Pattern**: All calculators **fail explicitly** with clear errors rather than using fallback values.

---

## Multi-State Model Current State

### What We Have ✅

1. **Training Data** (`data/processed/combined_with_competitive_features_corrected.csv`)
   - 741 dispensaries (FL + PA) with ALL required features already calculated
   - Columns include: `pop_1mi`, `pop_3mi`, `pop_5mi`, `pop_10mi`, `pop_20mi`
   - Columns include: `competitors_1mi`, `competitors_3mi`, etc.
   - Columns include: census demographics (age, income, education)
   - **Coordinates available**: `latitude`, `longitude` for all sites

2. **Census Data** (embedded in training data)
   - Census tract matching already performed during training
   - `census_geoid`, `census_tract_name` columns present
   - Demographics: `total_population`, `median_age`, `median_household_income`, etc.

3. **Feature Validator** (`src/prediction/feature_validator.py`)
   - Already generates 21 derived features automatically
   - Takes 23 base features → produces 44 total features
   - State indicators, interactions, saturation metrics

### What We Need to Build 🛠️

1. **Multi-State Data Loader** (new file: `src/feature_engineering/data_loader.py`)
   - Load FL + PA dispensaries for competition analysis
   - Load FL + PA census tracts for population analysis
   - Similar to PA model's `load_real_data()` method

2. **Coordinate-Based Calculator** (new file: `src/feature_engineering/coordinate_calculator.py`)
   - `calculate_population_multi_radius()` - Returns dict with pop_1mi, pop_3mi, etc.
   - `calculate_competitors_multi_radius()` - Returns dict with competitors_1mi, etc.
   - `calculate_competition_weighted()` - Distance-weighted score
   - `match_census_tract()` - Find nearest tract, extract demographics
   - **ALL methods return explicit errors if data unavailable**

3. **Enhanced CLI** (`src/terminal/cli.py` - modified)
   - Remove manual input for 23 base features
   - Accept: state, coordinates, sq_ft only
   - Call coordinate calculator for automatic feature generation
   - Handle errors gracefully (no fallbacks)

---

## Implementation Plan

### Phase 1: Data Infrastructure (New Files)

**File 1**: `src/feature_engineering/data_loader.py`
```python
class MultiStateDataLoader:
    """Load census and competition data for FL and PA."""

    def __init__(self):
        self.fl_dispensaries = None
        self.pa_dispensaries = None
        self.fl_census = None
        self.pa_census = None

    def load_dispensary_data(self):
        """Load FL and PA dispensaries for competition analysis."""
        # Extract from combined_with_competitive_features_corrected.csv
        # Filter: has_placer_data == True (verified locations)
        # Columns needed: state, latitude, longitude, regulator_name

    def load_census_data(self):
        """Load FL and PA census tracts for population analysis."""
        # Extract unique census tracts from training data
        # Group by census_geoid to get tract centroids
        # Store: geoid, lat, lon, total_population, demographics

    def get_state_data(self, state):
        """Return dispensaries and census data for specified state."""
        # Returns: (dispensaries_df, census_df) for state
        # Raises explicit error if state not FL or PA
```

**File 2**: `src/feature_engineering/coordinate_calculator.py`
```python
class CoordinateFeatureCalculator:
    """Calculate features from coordinates - NO FALLBACKS."""

    def __init__(self, data_loader):
        self.data_loader = data_loader

    def calculate_all_features(self, state, latitude, longitude):
        """
        Calculate all 23 base features from coordinates.

        Returns:
        --------
        dict with keys:
            - sq_ft (default: median by state, overridable)
            - pop_1mi, pop_3mi, pop_5mi, pop_10mi, pop_20mi
            - competitors_1mi, competitors_3mi, etc.
            - competition_weighted_20mi
            - total_population, median_age, median_household_income
            - per_capita_income, total_pop_25_plus
            - bachelors_degree, masters_degree, professional_degree, doctorate_degree
            - population_density, tract_area_sqm

        Raises:
        -------
        ValueError: If state not supported
        DataNotFoundError: If no census tract within 5 miles (explicit error, NO fallback)
        """

    def calculate_population_multi_radius(self, state, coords):
        """Calculate population at 1, 3, 5, 10, 20 mile radii."""
        # Use geodesic distance calculation
        # Sum all census tracts within each radius
        # Return dict: {'pop_1mi': X, 'pop_3mi': Y, ...}

    def calculate_competitors_multi_radius(self, state, coords):
        """Calculate competitors at 1, 3, 5, 10, 20 mile radii."""
        # Exclude self (distance > 0.1 miles)
        # Count dispensaries within each radius
        # Return dict: {'competitors_1mi': X, ...}

    def calculate_competition_weighted(self, state, coords, radius=20):
        """Calculate distance-weighted competition score."""
        # Sum of 1/distance for each competitor within radius
        # Formula: sum(1 / (distance + 0.01) for each competitor)

    def match_census_tract(self, state, coords):
        """Find nearest census tract and extract demographics."""
        # Find closest census tract within 5 miles
        # If none found: raise DataNotFoundError (NO FALLBACK)
        # Return all demographic fields
```

**Error Handling Class**: `src/feature_engineering/exceptions.py`
```python
class DataNotFoundError(Exception):
    """Raised when required data cannot be found - NO FALLBACK allowed."""
    pass

class InvalidStateError(Exception):
    """Raised when state is not FL or PA."""
    pass
```

---

### Phase 2: CLI Enhancement

**Modified File**: `src/terminal/cli.py`

**Changes**:

1. **Import new modules**:
   ```python
   from src.feature_engineering.data_loader import MultiStateDataLoader
   from src.feature_engineering.coordinate_calculator import CoordinateFeatureCalculator
   from src.feature_engineering.exceptions import DataNotFoundError, InvalidStateError
   ```

2. **Initialize in `__init__()`**:
   ```python
   def __init__(self):
       print("\n🔄 Loading model and data sources...")
       self.predictor = MultiStatePredictor()
       self.validator = FeatureValidator()

       # NEW: Load census and competition data
       self.data_loader = MultiStateDataLoader()
       self.calculator = CoordinateFeatureCalculator(self.data_loader)
       print("✅ Model and data loaded successfully\n")
   ```

3. **Replace `prompt_base_features()` with `prompt_coordinates_only()`**:
   ```python
   def prompt_coordinates_only(self, state):
       """Simplified input: only coordinates and optional sq_ft."""
       print("\n--- Site Location ---")

       # Get coordinates
       while True:
           coords_input = input("> Coordinates (lat, lon): ").strip().lower()
           if coords_input == 'cancel':
               return None
           try:
               lat, lon = parse_coordinates(coords_input)
               break
           except ValueError as e:
               print(f"  ❌ {e}")

       # Get square footage (optional, use state median if not provided)
       sq_ft_input = input("> Square footage (press Enter for default): ").strip()
       if sq_ft_input:
           sq_ft = float(sq_ft_input)
       else:
           sq_ft = None  # Will use state median

       return {'latitude': lat, 'longitude': lon, 'sq_ft': sq_ft}
   ```

4. **Auto-calculate features**:
   ```python
   def run_single_site_analysis(self):
       """Interactive single-site prediction with auto-calculated features."""
       state = self.prompt_state()
       if state is None:
           return

       coords = self.prompt_coordinates_only(state)
       if coords is None:
           return

       # AUTO-CALCULATE all features from coordinates
       print("\n🔄 Calculating features from coordinates...")
       try:
           base_features = self.calculator.calculate_all_features(
               state,
               coords['latitude'],
               coords['longitude']
           )

           # Override sq_ft if user provided
           if coords['sq_ft'] is not None:
               base_features['sq_ft'] = coords['sq_ft']

           print("✅ Features calculated successfully")
           print(f"  • Population (5mi): {base_features['pop_5mi']:,}")
           print(f"  • Competitors (5mi): {base_features['competitors_5mi']}")
           print(f"  • Census tract: {base_features.get('census_tract_name', 'N/A')}")

       except DataNotFoundError as e:
           print(f"\n❌ DATA ERROR: {e}")
           print("  Cannot proceed without required data.")
           print("  Recommendation: Verify coordinates are in FL or PA.")
           return
       except InvalidStateError as e:
           print(f"\n❌ INVALID STATE: {e}")
           return
       except Exception as e:
           print(f"\n❌ CALCULATION ERROR: {e}")
           return

       # Continue with validation and prediction...
   ```

---

### Phase 3: Data Validation Safeguards

**Critical Principle**: **NO FALLBACKS, EXPLICIT ERRORS ONLY**

**Safeguards to Implement**:

1. **Census Tract Matching**:
   ```python
   # BAD (fallback):
   if nearest_tract_distance > 5:
       # Use state median demographics
       demographics = get_state_medians(state)

   # GOOD (explicit error):
   if nearest_tract_distance > 5:
       raise DataNotFoundError(
           f"No census tract found within 5 miles of coordinates "
           f"({latitude:.4f}, {longitude:.4f}). "
           f"Verify coordinates are within {state}."
       )
   ```

2. **Competition Data**:
   ```python
   # BAD (fallback):
   if competitors_5mi == 0:
       competitors_5mi = 1  # Assume at least one competitor

   # GOOD (no fallback needed, 0 is valid):
   competitors_5mi = count_competitors(coords, 5)
   # 0 is a valid value (rural area, no competition)
   ```

3. **Population Data**:
   ```python
   # BAD (fallback):
   if pop_5mi == 0:
       pop_5mi = 10000  # Use minimum threshold

   # GOOD (explicit error if suspicious):
   if pop_5mi == 0:
       raise DataNotFoundError(
           f"No population found within 5 miles. "
           f"Coordinates may be invalid or in unpopulated area."
       )
   ```

4. **State Validation**:
   ```python
   # BAD (silent fallback):
   if state not in ['FL', 'PA']:
       state = 'FL'  # Default to FL

   # GOOD (explicit error):
   if state not in ['FL', 'PA']:
       raise InvalidStateError(
           f"State '{state}' not supported. "
           f"Model only supports FL and PA."
       )
   ```

**Error Message Format**:
```
❌ DATA ERROR: No census tract found within 5 miles of coordinates (28.5383, -81.3792).

Details:
  • State: FL
  • Nearest tract: 6.2 miles away (outside threshold)
  • Recommendation: Verify coordinates are correct

Cannot proceed without census demographic data.
```

---

## Data Sources

### Census Data Extraction

**Source**: `data/processed/combined_with_competitive_features_corrected.csv`

**Approach**: Extract unique census tracts with demographics
```python
# Pseudo-code for data extraction
census_df = training_df[
    ['state', 'census_geoid', 'census_tract_name', 'latitude', 'longitude',
     'total_population', 'median_age', 'median_household_income',
     'per_capita_income', 'total_pop_25_plus', 'bachelors_degree',
     'masters_degree', 'professional_degree', 'doctorate_degree',
     'population_density', 'tract_area_sqm']
].drop_duplicates(subset=['census_geoid'])

# Calculate tract centroids (average of all dispensaries in tract)
census_df = census_df.groupby('census_geoid').agg({
    'state': 'first',
    'census_tract_name': 'first',
    'latitude': 'mean',  # Centroid latitude
    'longitude': 'mean',  # Centroid longitude
    'total_population': 'first',
    # ... all other demographics
}).reset_index()
```

**Expected Output**: ~500-700 unique census tracts (FL + PA)

### Competition Data Extraction

**Source**: Same CSV file

**Approach**: Extract all verified dispensary locations
```python
dispensaries_df = training_df[
    training_df['has_placer_data'] == True
][['state', 'latitude', 'longitude', 'regulator_name', 'placer_name']]

# Result: ~741 verified dispensaries (FL + PA)
```

---

## Testing Strategy

### Unit Tests

1. **Test `calculate_population_multi_radius()`**:
   - Known coordinates → verify population totals match training data
   - Test all 5 radii (1, 3, 5, 10, 20 mi)
   - Verify populations are cumulative (pop_5mi >= pop_3mi)

2. **Test `calculate_competitors_multi_radius()`**:
   - Known dispensary location → verify competitor counts
   - Test self-exclusion (distance > 0.1 mi)
   - Verify cumulative counts

3. **Test `match_census_tract()`**:
   - Known coordinates → verify correct tract matched
   - Test error raised when no tract within 5 miles
   - Test demographics extracted correctly

4. **Test error handling**:
   - Invalid state → InvalidStateError
   - Remote coordinates → DataNotFoundError
   - Verify NO fallbacks in any scenario

### Integration Tests

1. **Test full feature calculation**:
   - Use known Insa store coordinates
   - Compare auto-calculated features to training data
   - Verify predictions match

2. **Test CLI workflow**:
   - Input coordinates only
   - Verify all 23 base features calculated
   - Verify prediction generated
   - Verify errors displayed correctly

---

## Success Criteria

### Functional Requirements ✅

1. **User inputs only 3-4 values** (state, coordinates, optional sq_ft)
2. **System calculates 23 base features automatically**
3. **Feature generation completes in < 5 seconds per site**
4. **Errors are explicit and informative (no fallbacks)**
5. **Predictions match existing model performance**

### Data Quality Requirements ✅

1. **Census matching accuracy**: 95%+ within 2 miles of nearest tract
2. **Population calculation**: Matches training data within ±5%
3. **Competition calculation**: Exact match to manual counts
4. **Zero synthetic data**: All calculations use real data only

### User Experience Requirements ✅

1. **Clear progress indicators** during calculation
2. **Informative error messages** with recommendations
3. **Feature summary displayed** before prediction
4. **Maintains PA model's proven UX pattern**

---

## Implementation Timeline

### Phase 1: Data Infrastructure (1-2 hours)
- [ ] Create `data_loader.py`
- [ ] Extract census data from training CSV
- [ ] Extract dispensary data from training CSV
- [ ] Test data loading

### Phase 2: Feature Calculation (2-3 hours)
- [ ] Create `coordinate_calculator.py`
- [ ] Implement population calculation
- [ ] Implement competitor calculation
- [ ] Implement census tract matching
- [ ] Implement distance-weighted competition
- [ ] Add error handling (no fallbacks)

### Phase 3: CLI Integration (1-2 hours)
- [ ] Modify `cli.py` to use coordinate calculator
- [ ] Update `run_single_site_analysis()`
- [ ] Update `run_batch_analysis()` (CSV with coordinates)
- [ ] Test end-to-end workflow

### Phase 4: Testing & Validation (1-2 hours)
- [ ] Unit tests for all calculators
- [ ] Integration test with known Insa locations
- [ ] Verify predictions match training data
- [ ] Test error scenarios

**Total Estimated Time**: 5-9 hours

---

## Risks & Mitigations

### Risk 1: Census Tract Data Quality
**Concern**: Training data census coordinates may not represent tract centroids accurately.

**Mitigation**:
- Use average of all dispensaries in tract as centroid
- Allow 5-mile search radius for tract matching
- Log warnings when match distance > 2 miles

### Risk 2: Performance (Calculation Speed)
**Concern**: Iterating through 700+ census tracts for each site could be slow.

**Mitigation**:
- Use spatial indexing (optional: `scipy.spatial.cKDTree`)
- Pre-filter by state before distance calculations
- Expected: < 2 seconds per site (acceptable)

### Risk 3: Edge Cases (Remote Locations)
**Concern**: Rural coordinates may have no census tract within 5 miles.

**Mitigation**:
- **Do NOT use fallback values**
- Raise explicit `DataNotFoundError`
- User must verify coordinates or accept limitation

---

## Future Enhancements (Post-MVP)

1. **Traffic Data Integration** (like PA model)
   - Integrate real traffic data for FL + PA
   - Requires sourcing FL DOT AADT data
   - Add traffic feature to model

2. **Census API Real-Time Lookup**
   - For coordinates not in training data
   - Fetch demographics directly from Census API
   - Backup when tract not in cached data

3. **Batch CSV with Coordinates**
   - Accept CSV with just: state, lat, lon, sq_ft
   - Auto-calculate all features for batch analysis

4. **Address Geocoding**
   - Accept street address
   - Auto-geocode to coordinates
   - Requires geocoding API (Google, Census, etc.)

---

## Conclusion

This implementation transforms the Multi-State Dispensary Model CLI from **impractical** (23 manual inputs) to **production-ready** (3-4 inputs) by automating feature calculation from coordinates.

**Key Principles**:
1. ✅ **Real data only** - no synthetic estimates
2. ✅ **Explicit errors** - no fallback values
3. ✅ **Proven pattern** - mirrors PA model success
4. ✅ **Fast execution** - < 5 seconds per site

**Next Step**: Begin Phase 1 implementation upon approval.

---

**Document Status**: Ready for Review
**Approval Required**: Yes (Daniel)
**Implementation Start**: Upon approval
