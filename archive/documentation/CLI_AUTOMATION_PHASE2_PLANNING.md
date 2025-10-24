# CLI Automation Continuation Prompt
## Resume Phase 2 Implementation After Compacting

**Date Created**: October 24, 2025
**Current Status**: Phase 1 Complete ✅ | Phase 2 Ready to Start
**Use This**: After compacting to resume CLI automation work

---

## Quick Start Continuation Prompt

Copy/paste this after compacting:

> **"CLI automation Phase 1 complete. Data infrastructure ready with 7,624 census tracts. Please proceed with Phase 2: coordinate-based feature calculator. See docs/CLI_AUTOMATION_CONTINUATION_PROMPT.md for context."**

---

## Current Project State

### What's Complete ✅

**Phase 1: Data Infrastructure** (Complete - October 24, 2025)
- ✅ `src/feature_engineering/exceptions.py` - Custom error classes (no fallbacks)
- ✅ `src/feature_engineering/data_loader.py` - Multi-state data loader (7,624 census tracts)
- ✅ `tests/test_data_loader.py` - Comprehensive test suite (8 tests passing)
- ✅ Codex review fix applied: Census coverage 600 → 7,624 tracts (12.7x improvement)
- ✅ Documentation complete: Implementation plan, completion report, fix documentation

**Key Achievement**:
- 100% FL/PA geographic coverage (4,983 FL + 2,641 PA census tracts)
- 741 dispensaries loaded for competition analysis
- Ready for coordinate-based feature calculation

### What's Next 🔜

**Phase 2: Coordinate-Based Feature Calculator** (2-3 hours estimated)

**Goal**: Build calculator that takes coordinates and automatically generates all 23 base features (population, competition, demographics) needed for model prediction.

**Components to Build**:
1. `src/feature_engineering/coordinate_calculator.py` (~400-500 lines)
   - `calculate_population_multi_radius(state, coords)` - Sum census populations within 1, 3, 5, 10, 20 mile radii
   - `calculate_competitors_multi_radius(state, coords)` - Count dispensaries within same radii
   - `calculate_competition_weighted(state, coords, radius=20)` - Distance-weighted competition score
   - `match_census_tract(state, coords)` - Use Census Geocoding API to get GEOID, lookup demographics
   - `calculate_all_features(state, lat, lon, sq_ft=None)` - Master method returning all 23 features

2. Unit tests for each method (~200-300 lines)

3. Integration tests with known Insa locations

---

## Architecture Reference

### Data Flow

```
User Input:
  • State (FL or PA)
  • Coordinates (latitude, longitude)
  • Square footage (optional)
    ↓
Phase 2: Coordinate Calculator
  ├─→ calculate_population_multi_radius()
  │   └─→ Returns: pop_1mi, pop_3mi, pop_5mi, pop_10mi, pop_20mi
  ├─→ calculate_competitors_multi_radius()
  │   └─→ Returns: competitors_1mi through competitors_20mi
  ├─→ calculate_competition_weighted()
  │   └─→ Returns: competition_weighted_20mi
  └─→ match_census_tract()
      └─→ Census API → GEOID → demographics lookup
          Returns: 11 demographic fields
    ↓
Complete Features: 23 base features
    ↓
Phase 1: Feature Validator (already exists)
  └─→ Generates 21 derived features
    ↓
Total: 44 features ready for prediction
```

### Census Tract Lookup Strategy

**DO NOT** try to match coordinates to nearest census tract centroid.

**DO** use Census Geocoding API:
1. Call API: `https://geocoding.geo.census.gov/geocoder/geographies/coordinates`
2. Get census_geoid from response
3. Look up demographics in loaded data: `census_df[census_df['census_geoid'] == geoid]`

**Why**: Census tracts are polygons (not points). API provides exact tract identification.

**Infrastructure**: `CensusTractIdentifier` class already exists in `src/feature_engineering/census_tract_identifier.py`

---

## Key Files Reference

### Phase 1 Files (Already Complete)
```
src/feature_engineering/
├── exceptions.py                  # Custom error classes
├── data_loader.py                 # Multi-state data loader (7,624 tracts)
└── census_tract_identifier.py    # Census API wrapper (from Phase 2)

tests/
└── test_data_loader.py            # Data loader tests (8 passing)

docs/
├── CLI_AUTOMATION_IMPLEMENTATION_PLAN.md    # Complete plan (all 4 phases)
├── PHASE1_DATA_INFRASTRUCTURE_COMPLETE.md   # Phase 1 completion
└── PHASE1_CODEX_REVIEW_FIX.md              # Coverage fix (600→7,624)
```

### Phase 2 Files (To Be Created)
```
src/feature_engineering/
└── coordinate_calculator.py       # NEW - Feature calculator

tests/
└── test_coordinate_calculator.py  # NEW - Calculator tests
```

---

## Implementation Checklist for Phase 2

### Step 1: Create coordinate_calculator.py Structure
```python
class CoordinateFeatureCalculator:
    def __init__(self, data_loader):
        """Initialize with data_loader from Phase 1"""
        self.data_loader = data_loader
        self.census_identifier = CensusTractIdentifier()

    def calculate_all_features(self, state, latitude, longitude, sq_ft=None):
        """Master method - returns all 23 base features"""
        pass
```

### Step 2: Implement Population Calculation
```python
def calculate_population_multi_radius(self, state, coords):
    """
    Calculate population at 1, 3, 5, 10, 20 mile radii.

    Returns:
        dict: {'pop_1mi': X, 'pop_3mi': Y, 'pop_5mi': Z, ...}
    """
    # 1. Get state census data from data_loader
    # 2. For each radius (1, 3, 5, 10, 20):
    #    - For each census tract:
    #      - Calculate distance using geodesic()
    #      - If within radius, add population
    # 3. Return dict with 5 population values
```

### Step 3: Implement Competition Calculation
```python
def calculate_competitors_multi_radius(self, state, coords):
    """
    Calculate competitor counts at 1, 3, 5, 10, 20 mile radii.

    Returns:
        dict: {'competitors_1mi': X, 'competitors_3mi': Y, ...}
    """
    # Similar to population, but count dispensaries
    # Exclude self (distance > 0.1 miles)
```

### Step 4: Implement Distance-Weighted Competition
```python
def calculate_competition_weighted(self, state, coords, radius=20):
    """
    Calculate distance-weighted competition score.

    Formula: sum(1 / (distance + 0.01) for each competitor)
    """
```

### Step 5: Implement Census Tract Matching
```python
def match_census_tract(self, state, coords):
    """
    Find census tract and extract demographics.

    Uses Census Geocoding API, then looks up demographics.

    Raises:
        DataNotFoundError: If no tract found (NO FALLBACK)
    """
    # 1. Call census_identifier.get_tract_from_coordinates()
    # 2. Extract census_geoid from response
    # 3. Look up in census_df by geoid
    # 4. If not found, raise DataNotFoundError
    # 5. Return all demographic fields
```

### Step 6: Implement Master Method
```python
def calculate_all_features(self, state, latitude, longitude, sq_ft=None):
    """
    Calculate all 23 base features from coordinates.

    Returns:
        dict with all 23 base features ready for feature_validator
    """
    # 1. Validate state
    # 2. Validate coordinates
    # 3. Call calculate_population_multi_radius()
    # 4. Call calculate_competitors_multi_radius()
    # 5. Call calculate_competition_weighted()
    # 6. Call match_census_tract()
    # 7. Get sq_ft (use state median if not provided)
    # 8. Combine all into dict with 23 keys
    # 9. Return
```

### Step 7: Write Tests
- Test each method independently
- Test with known Insa store coordinates
- Verify calculations match training data
- Test error handling (invalid state, remote coordinates, etc.)

---

## Critical Principles

### 1. No Fallback Values
```python
# ❌ WRONG:
if no_census_tract_found:
    demographics = get_state_defaults()

# ✅ CORRECT:
if no_census_tract_found:
    raise DataNotFoundError("No census tract within 5 miles")
```

### 2. Explicit Errors
All errors must be clear and actionable:
```
❌ DATA ERROR: No census tract found within 5 miles

Details:
  • State: FL
  • Coordinates: (28.5383, -81.3792)
  • Nearest tract: 6.2 miles away

Cannot proceed without census demographic data.
```

### 3. Use Real Data Only
- Population: Sum from census tracts
- Competition: Count from dispensary database
- Demographics: From Census API + cached data
- NO synthetic data, NO estimates, NO defaults

---

## Expected Timeline

### Phase 2: Coordinate Calculator (2-3 hours)
- Hour 1: Create structure + population/competition calculators
- Hour 2: Census tract matching + master method
- Hour 3: Testing and validation

### Phase 3: CLI Integration (1-2 hours)
- Modify `src/terminal/cli.py` to use calculator
- Remove 23-input prompts, add coordinate input
- Test end-to-end workflow

### Phase 4: Testing & Validation (1-2 hours)
- Integration tests with known locations
- Batch CSV testing
- Documentation updates

**Total Remaining**: 4-7 hours

---

## Testing Strategy

### Unit Tests
```python
def test_population_calculation():
    # Use known Insa store coordinates
    # Verify population totals match training data
    # Check all 5 radii

def test_competitor_calculation():
    # Use known dispensary location
    # Verify competitor counts
    # Check self-exclusion (distance > 0.1)

def test_census_tract_matching():
    # Use coordinates from training data
    # Verify correct tract matched
    # Check demographics extracted correctly

def test_error_handling():
    # Test invalid state → InvalidStateError
    # Test remote coordinates → DataNotFoundError
    # Verify NO fallbacks used
```

### Integration Tests
```python
def test_full_feature_generation():
    # Use Insa Orlando store: (28.5685, -81.2163)
    # Generate all 23 features
    # Compare to training data row
    # Verify within ±5% (acceptable variance)
```

---

## Success Criteria

### Functional Requirements
- [ ] User inputs only state + coordinates + optional sq_ft (3-4 inputs)
- [ ] System calculates all 23 base features automatically
- [ ] Feature generation completes in < 5 seconds per site
- [ ] Errors are explicit and informative (no fallbacks)
- [ ] Predictions match existing model performance

### Data Quality Requirements
- [ ] Census matching accuracy: 95%+ within 2 miles of nearest tract
- [ ] Population calculation: Matches training data within ±5%
- [ ] Competition calculation: Exact match to manual counts
- [ ] Zero synthetic data used

### User Experience Requirements
- [ ] Clear progress indicators during calculation
- [ ] Informative error messages with recommendations
- [ ] Feature summary displayed before prediction
- [ ] Maintains proven PA model UX pattern

---

## Common Pitfalls to Avoid

1. **Don't try to match coordinates to census centroids** - Use Census API instead
2. **Don't use fallback values when data is missing** - Raise explicit errors
3. **Don't forget self-exclusion in competition** - distance > 0.1 miles
4. **Don't use approximate distance** - Use geodesic (Haversine formula)
5. **Don't skip validation** - All inputs must be validated

---

## Quick Reference Commands

```bash
# Test data loader (Phase 1 - already passing)
python3 tests/test_data_loader.py

# Test coordinate calculator (Phase 2 - to be created)
python3 tests/test_coordinate_calculator.py

# Run enhanced CLI (Phase 3 - future)
python3 src/terminal/cli.py
```

---

## Documentation References

**Full Implementation Plan**: `docs/CLI_AUTOMATION_IMPLEMENTATION_PLAN.md`
**Phase 1 Complete**: `docs/PHASE1_DATA_INFRASTRUCTURE_COMPLETE.md`
**Codex Fix**: `docs/PHASE1_CODEX_REVIEW_FIX.md`

---

**Status**: Ready for Phase 2 Implementation
**Last Updated**: October 24, 2025
**Next Session**: Implement coordinate_calculator.py
