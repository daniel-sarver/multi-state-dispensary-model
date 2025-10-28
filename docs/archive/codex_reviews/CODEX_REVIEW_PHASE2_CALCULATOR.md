# Codex Review: CLI Automation Phase 2 Calculator
## Critical Centroid Issue Identified

**Review Date**: October 24, 2025
**Reviewer**: Codex
**Phase**: CLI Automation Phase 2 - Coordinate Calculator
**Status**: 🔴 **CRITICAL ISSUE** - Must fix before Phase 3

---

## Executive Summary

Phase 2 coordinate calculator has a **critical flaw** in census tract centroid loading that makes population calculations at small radii (1-10 mi) **unusable**. The current implementation falls back to county-level approximations that collapse thousands of tracts into a handful of coordinate pairs, causing dramatic undercounting and artificially flattened competition metrics.

**Impact**: Phase 2 output is not production-ready. Must fix centroid loading before proceeding to Phase 3.

---

## Critical Findings

### 1. County-Level Centroid Fallback Creates Massive Data Collapse

**Location**: `src/feature_engineering/data_loader.py:221-320` (`_add_approximate_centroids()`)

**Issue**: The fallback centroid dictionary only lists ~8 major counties per state. As a result:

- **Florida**: 4,983 tracts collapse into ~8 coordinate pairs
  - Example: 2,637 tracts all mapped to `(28.0000, -82.0000)` (state center)
- **Pennsylvania**: 2,641 tracts collapse into ~8 coordinate pairs
  - Most tracts mapped to `(40.5000, -77.5000)` (state center)

**Code Example**:
```python
# From data_loader.py - PROBLEMATIC
county_centers = {
    # Florida - only 7 counties defined
    ('12', '011'): (26.6706, -80.0933),  # Broward
    ('12', '086'): (27.9506, -82.4572),  # Miami-Dade
    # ... only 5 more ...

    # Pennsylvania - only 7 counties defined
    ('42', '003'): (40.4686, -79.9375),  # Allegheny
    # ... only 6 more ...
}

# State default centers (used for 90%+ of tracts!)
state_centers = {
    '12': (28.0, -82.0),  # FL - 2,637+ tracts use this
    '42': (40.5, -77.5),  # PA - 2,000+ tracts use this
}
```

**Impact on Population Calculations**:

When `calculate_population_multi_radius()` calculates distance from user coordinates to tract centroids:

1. **Almost all tracts appear to be at the same location** (state center)
2. Distance calculations become meaningless
3. For small radii (1-10 mi):
   - Most tracts are exactly the same distance away
   - Either ALL included or ALL excluded based on that single distance
   - **Result**: Dramatic undercounting (or overcounting in rare cases)

**Example**:
```
User coordinates: Orlando (28.5685, -81.2163)
Tract centroids: 2,637 tracts at (28.0, -82.0) - ~58 miles away
Result for 5mi radius: 0 population (should be ~100,000+)
Result for 10mi radius: 0 population (should be ~500,000+)
Result for 20mi radius: 1,440,471 (happens to work because state center IS within 20mi)
```

### 2. Fetch Script Doesn't Actually Fetch

**Location**: `scripts/fetch_tract_centroids.py`

**Issue**: The script simply instantiates `MultiStateDataLoader`, which triggers the same county-level fallback logic. No TIGER/Gazetteer lookups actually happen.

**Code**:
```python
# From fetch_tract_centroids.py - DOESN'T FIX THE PROBLEM
loader = MultiStateDataLoader()  # Just uses same county fallbacks!
```

**Impact**: Running this script produces the same coarse county centroids. Does not improve accuracy at all.

### 3. Competition Metrics Artificially Flattened

**Impact**: Because all tracts appear to be at ~8 locations, competition calculations also become unreliable:
- Competitors per 100k population metrics are based on collapsed populations
- Distance-weighted competition scores don't reflect true competitive landscape
- Rankings between sites become questionable

---

## Root Cause Analysis

### Why This Happened

**Original Design Intent** (from Phase 2 implementation):
1. Use approximate centroids for **fast initial testing**
2. Provide `fetch_tract_centroids.py` script to **upgrade to exact centroids**
3. Cache exact centroids for **future use**

**What Actually Happened**:
1. ✅ Approximate centroids are fast (instant loading)
2. ❌ Approximate centroids are WAY too approximate (county/state level)
3. ❌ Fetch script doesn't actually fetch (just uses same approximations)
4. ❌ No path to get real centroids (cache never gets populated)

**Lesson**: "Approximate" should mean ~100m error, not ~10km error. County-level is not suitable even for testing.

---

## Path Forward

### Immediate Actions Required

#### 1. Source Authoritative Tract Centroids

**Option A: Census Gazetteer Files** (Recommended - Fastest)

Files already partially downloaded:
- `data/census/gazeteer/2020_Gaz_tracts_12.txt` (exists but corrupted - HTML instead of data)
- `data/census/gazeteer/2020_Gaz_tracts_42.txt` (missing)

**Action**:
```bash
# Download correct Gazetteer files
curl "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_tracts_12.txt" \
     -o data/census/gazeteer/2020_Gaz_tracts_12.txt

curl "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_tracts_42.txt" \
     -o data/census/gazeteer/2020_Gaz_tracts_42.txt
```

**Format**:
```
GEOID       NAME            INTPTLAT    INTPTLONG
12001950100 950100          25.761681   -80.191788
```

**Option B: TIGER/Line Shapefiles** (Already have these!)

Location: `data/census/tract_shapefiles/`

**Action**:
```python
import geopandas as gpd

# Load FL shapefile
fl_tracts = gpd.read_file("data/census/tract_shapefiles/tl_2020_12_tract/tl_2020_12_tract.shp")
fl_centroids = fl_tracts.geometry.centroid
fl_tracts['latitude'] = fl_centroids.y
fl_tracts['longitude'] = fl_centroids.x

# Extract GEOID, lat, lon
centroids_df = fl_tracts[['GEOID', 'latitude', 'longitude']]
```

**Recommendation**: Use **Option A (Gazetteer)** - simpler, faster, no shapefile parsing needed.

#### 2. Fix Data Loader Centroid Logic

**Changes Required in `data_loader.py`**:

```python
def _add_tract_centroids(self, census: pd.DataFrame) -> pd.DataFrame:
    """
    Add latitude/longitude centroids for census tracts.

    CRITICAL: Must use real per-tract centroids, not county approximations.
    """
    print("    • Loading census tract centroids...")

    # Check cache first
    cache_file = self.project_root / "data" / "census" / "cache" / "tract_centroids.csv"
    if cache_file.exists():
        centroids_df = pd.read_csv(cache_file, dtype={'census_geoid': str})
        census = census.merge(centroids_df[['census_geoid', 'latitude', 'longitude']],
                             on='census_geoid', how='left')

        missing = census['latitude'].isna().sum()
        if missing == 0:
            print(f"      ✓ All {len(census)} tract centroids loaded from cache")
            return census

    # Load from Gazetteer files (authoritative source)
    print(f"      Loading centroids from Census Gazetteer files...")
    census = self._load_centroids_from_gazetteer(census)

    # Save to cache
    self._save_centroid_cache(census)

    return census

def _load_centroids_from_gazetteer(self, census: pd.DataFrame) -> pd.DataFrame:
    """
    Load real per-tract centroids from Census Gazetteer files.

    NO FALLBACKS - if Gazetteer files missing, raise error.
    """
    fl_gaz = self.project_root / "data" / "census" / "gazeteer" / "2020_Gaz_tracts_12.txt"
    pa_gaz = self.project_root / "data" / "census" / "gazeteer" / "2020_Gaz_tracts_42.txt"

    # Check files exist
    if not fl_gaz.exists() or not pa_gaz.exists():
        raise FileNotFoundError(
            f"Census Gazetteer files not found!\n\n"
            f"Required files:\n"
            f"  • {fl_gaz}\n"
            f"  • {pa_gaz}\n\n"
            f"Download with:\n"
            f"  bash scripts/download_gazetteer_files.sh\n\n"
            f"Or manually from:\n"
            f"  https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/"
        )

    # Load FL centroids
    fl_centroids = pd.read_csv(fl_gaz, sep='\t', dtype={'GEOID': str})
    fl_centroids = fl_centroids[['GEOID', 'INTPTLAT', 'INTPTLONG']].rename(
        columns={'GEOID': 'census_geoid', 'INTPTLAT': 'latitude', 'INTPTLONG': 'longitude'}
    )

    # Load PA centroids
    pa_centroids = pd.read_csv(pa_gaz, sep='\t', dtype={'GEOID': str})
    pa_centroids = pa_centroids[['GEOID', 'INTPTLAT', 'INTPTLONG']].rename(
        columns={'GEOID': 'census_geoid', 'INTPTLAT': 'latitude', 'INTPTLONG': 'longitude'}
    )

    # Combine
    all_centroids = pd.concat([fl_centroids, pa_centroids], ignore_index=True)

    # Merge with census data
    census = census.merge(all_centroids, on='census_geoid', how='left')

    # Check for missing
    missing = census['latitude'].isna().sum()
    if missing > 0:
        print(f"      ⚠️  {missing} tracts missing centroids (expected for water/unpopulated areas)")

    print(f"      ✓ Loaded {len(census) - missing} tract centroids from Gazetteer files")

    return census
```

**Key Changes**:
1. ❌ **Remove** `_add_approximate_centroids()` - no more county fallbacks
2. ❌ **Remove** `_add_tract_centroids_via_api()` - too slow, not needed
3. ✅ **Add** `_load_centroids_from_gazetteer()` - authoritative source
4. ✅ **Require** Gazetteer files - fail fast if missing

#### 3. Create Gazetteer Download Script

**New file**: `scripts/download_gazetteer_files.sh`

```bash
#!/bin/bash
# Download Census Gazetteer tract centroid files for FL and PA

echo "Downloading Census Gazetteer files..."

mkdir -p data/census/gazeteer

# Download FL
echo "  Downloading Florida (12)..."
curl -o data/census/gazeteer/2020_Gaz_tracts_12.txt \
     "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_tracts_12.txt"

# Download PA
echo "  Downloading Pennsylvania (42)..."
curl -o data/census/gazeteer/2020_Gaz_tracts_42.txt \
     "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_tracts_42.txt"

echo "✓ Gazetteer files downloaded"
echo ""
echo "Files:"
wc -l data/census/gazeteer/2020_Gaz_tracts_*.txt
```

#### 4. Fix Fetch Script

**Update**: `scripts/fetch_tract_centroids.py`

```python
"""
This script is NO LONGER NEEDED.

Census tract centroids are now loaded automatically from Gazetteer files
when you first run the coordinate calculator.

If Gazetteer files are missing, run:
    bash scripts/download_gazetteer_files.sh

Or download manually from:
    https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/
"""

print("⚠️  This script is deprecated.")
print("")
print("Census tract centroids are now loaded automatically from Gazetteer files.")
print("")
print("If you need to download the Gazetteer files, run:")
print("    bash scripts/download_gazetteer_files.sh")
```

#### 5. Update Tests

**Add validation to `tests/test_data_loader.py`**:

```python
def test_centroid_uniqueness(loader):
    """Verify centroids are per-tract, not collapsed to county/state centers."""

    # Check FL centroids are unique
    fl_coords = loader.fl_census[['latitude', 'longitude']].drop_duplicates()

    # Should have thousands of unique coordinates, not ~8
    assert len(fl_coords) > 4000, \
        f"FL centroids collapsed! Only {len(fl_coords)} unique coords (expected ~4,983)"

    # Check PA centroids are unique
    pa_coords = loader.pa_census[['latitude', 'longitude']].drop_duplicates()

    assert len(pa_coords) > 2000, \
        f"PA centroids collapsed! Only {len(pa_coords)} unique coords (expected ~2,641)"

    print(f"  ✓ FL: {len(fl_coords)} unique tract centroids (expected ~4,983)")
    print(f"  ✓ PA: {len(pa_coords)} unique tract centroids (expected ~2,641)")
```

#### 6. Validation Tests

**After fixing, test with known site**:

```python
# Test: Insa Orlando
calculator = CoordinateFeatureCalculator()
features = calculator.calculate_all_features(
    state='FL',
    latitude=28.5685,
    longitude=-81.2163
)

# Validate against Phase 2 training data
# Insa Orlando is in training set - we can compare!
training_data = pd.read_csv('data/processed/combined_with_competitive_features_corrected.csv')
orlando = training_data[
    (training_data['latitude'].between(28.56, 28.58)) &
    (training_data['longitude'].between(-81.22, -81.21))
]

print("Validation:")
print(f"  Calculated pop_5mi: {features['pop_5mi']:,}")
print(f"  Training pop_5mi: {orlando['pop_5mi'].values[0]:,}")
print(f"  Difference: {abs(features['pop_5mi'] - orlando['pop_5mi'].values[0]):,}")

# Should be within 5% (different centroid precision, area-weighting, etc.)
assert abs(features['pop_5mi'] - orlando['pop_5mi'].values[0]) / orlando['pop_5mi'].values[0] < 0.05
```

---

## Implementation Priority

### Must Fix Before Phase 3 ❗

1. ✅ Download correct Gazetteer files
2. ✅ Fix `_add_tract_centroids()` to use Gazetteer
3. ✅ Remove county/state fallback logic
4. ✅ Create download script for Gazetteer files
5. ✅ Add centroid uniqueness test
6. ✅ Validate with known Insa Orlando site
7. ✅ Update documentation

**Estimated Time**: 30-60 minutes

### Can Do Later

- Deprecate `fetch_tract_centroids.py` script
- Add GeoPandas alternative for shapefile centroids
- Enhance error messages

---

## Revised Timeline

### Original Plan (Before Codex Review)
- Phase 2: ✅ Complete
- Phase 3: CLI Integration (1-2 hours)
- Phase 4: Testing (1-2 hours)

### Revised Plan (After Codex Review)
- **Phase 2 Fix**: Centroid loading (30-60 min) ← **DO THIS FIRST**
- Phase 2 Validation: Test with real centroids (15 min)
- Phase 3: CLI Integration (1-2 hours)
- Phase 4: Testing (1-2 hours)

**New Total**: Add 1 hour to original timeline

---

## Success Criteria (Updated)

### Phase 2 Cannot Be Considered Complete Until:

- [ ] Gazetteer files downloaded and verified
- [ ] Data loader uses per-tract centroids (not county fallbacks)
- [ ] Test shows 4,000+ unique FL centroids (not ~8)
- [ ] Test shows 2,000+ unique PA centroids (not ~8)
- [ ] Insa Orlando population calculations match Phase 2 training data (±5%)
- [ ] All 5 radii (1, 3, 5, 10, 20 mi) show reasonable populations (not zeros)

### Then Phase 3 Can Proceed

---

## Lessons Learned

1. **"Approximate" Needs Definition**: County-level approximations are not suitable even for testing. Should have been ~100m error, not ~10km.

2. **Verify Fallback Logic**: Always test that fallback values are actually reasonable. State center coordinates are not reasonable for per-tract calculations.

3. **Test Data Quality Early**: Should have tested centroid uniqueness immediately, not just end-to-end functionality.

4. **Scripts Should Do What They Say**: A script called `fetch_tract_centroids.py` should actually fetch centroids, not just instantiate existing logic.

5. **Fast ≠ Correct**: Instant loading is great, but not if it produces unusable data. Better to spend 1 minute downloading real data than have instant access to wrong data.

---

## Document History

- **Created**: October 24, 2025
- **Status**: Critical fix required
- **Next**: Implement fixes, revalidate Phase 2, then proceed to Phase 3

---

**Critical**: Do not proceed to Phase 3 CLI integration until centroid issue is fixed and validated.
