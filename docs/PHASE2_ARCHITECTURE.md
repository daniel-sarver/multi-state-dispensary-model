# Phase 2 Architecture: Census Demographics Integration

**Date**: October 22, 2025
**Status**: Design Phase
**Target**: Add demographic features to 741 training dispensaries

---

## Overview

This document outlines the technical architecture for collecting and integrating US Census Bureau demographic data with our combined dispensary datasets. The goal is to enhance model predictive power by adding population, age, income, education, and density features at multiple geographic scales.

---

## Data Sources

### 1. Census Geocoding API (Free, No Key Required)

**Purpose**: Convert dispensary coordinates to census tract FIPS codes

**Endpoint**:
```
https://geocoding.geo.census.gov/geocoder/geographies/coordinates
```

**Parameters**:
- `x`: Longitude (decimal)
- `y`: Latitude (decimal)
- `benchmark`: Use `Public_AR_Current` or `4` for current
- `vintage`: Use `Current_Current` or `4` for current geography
- `format`: `json`

**Example Request**:
```
https://geocoding.geo.census.gov/geocoder/geographies/coordinates?x=-80.191788&y=25.761681&benchmark=4&vintage=4&format=json
```

**Response Structure**:
```json
{
  "result": {
    "geographies": {
      "Census Tracts": [{
        "GEOID": "12086011702",
        "STATE": "12",
        "COUNTY": "086",
        "TRACT": "011702",
        "BASENAME": "117.02",
        ...
      }]
    }
  }
}
```

**Rate Limits**: Not specified; be considerate with batch requests

---

### 2. American Community Survey (ACS) 5-Year API

**Purpose**: Retrieve demographic variables at census tract level

**Endpoint**:
```
https://api.census.gov/data/2023/acs/acs5
```

**API Key**: Retrieved from environment variable `CENSUS_API_KEY`

**Security Note**:
- API key should NEVER be committed to Git
- Set environment variable: `export CENSUS_API_KEY=your_key_here`
- Add to `.gitignore`: `*.env`, `.env*`
- Python code should use: `os.environ.get("CENSUS_API_KEY")`

**Query Format**:
```
?get=VARIABLE1,VARIABLE2,...&for=tract:TRACT&in=state:STATE+county:COUNTY&key={CENSUS_API_KEY}
```

**Example Request**:
```python
import os
api_key = os.environ.get("CENSUS_API_KEY")
url = f"https://api.census.gov/data/2023/acs/acs5?get=NAME,B01001_001E,B19013_001E&for=tract:011702&in=state:12+county:086&key={api_key}"
```

**Response Format**:
```json
[
  ["NAME", "B01001_001E", "B19013_001E", "state", "county", "tract"],
  ["Census Tract 117.02, Miami-Dade County, Florida", "4521", "52000", "12", "086", "011702"]
]
```

**Rate Limits**: No documented hard limit, but recommended to stay under 500 requests/second

---

## Required Demographic Variables

### Core Variables

| Variable Code | Description | Usage |
|--------------|-------------|--------|
| **B01001_001E** | Total Population | Base for all calculations, population density |
| **B01002_001E** | Median Age | Age demographics |
| **B19013_001E** | Median Household Income | Income demographics |
| **B19301_001E** | Per Capita Income | Individual income level |
| **B15003_001E** | Total Population 25+ Years | Base for education calculations |
| **B15003_022E** | Bachelor's Degree | Education attainment |
| **B15003_023E** | Master's Degree | Education attainment |
| **B15003_024E** | Professional Degree | Education attainment |
| **B15003_025E** | Doctorate Degree | Education attainment |

### Derived Variables

| Derived Feature | Calculation | Purpose |
|----------------|-------------|---------|
| **pct_bachelor_plus** | (B15003_022E + 023E + 024E + 025E) / B15003_001E * 100 | % with bachelor's+ |
| **population_density** | B01001_001E / tract_area_sq_miles | People per sq mile |
| **pop_1mi** | Sum of population in tracts within 1-mile buffer | Immediate local market |
| **pop_3mi** | Sum of population in tracts within 3-mile buffer | Core trade area |
| **pop_5mi** | Sum of population in tracts within 5-mile buffer | Extended local market |
| **pop_10mi** | Sum of population in tracts within 10-mile buffer | Regional market |
| **pop_20mi** | Sum of population in tracts within 20-mile buffer | Destination market (rural/suburban) |

### Multi-Radius Strategy Rationale

Based on analysis of Insa Jacksonville trade area data:

**Trade Area Distribution** (Insa Jacksonville, FL):
- **0-1 mile**: ~17% of visits (immediate neighborhood)
- **1-2 miles**: ~17% of visits (local community)
- **3-5 miles**: ~26% combined (core trade area)
- **7-10 miles**: ~9% of visits (extended market)
- **30+ miles**: ~19% of visits (destination/regional draw)

**Radius Selection Logic**:
- **1mi**: Captures immediate walk-up and very local traffic
- **3mi**: Core convenience market (0.5-2mi combined = ~18%)
- **5mi**: Extended local market including 3-5mi zone (~13%)
- **10mi**: Regional suburban coverage (7-10mi = ~9%)
- **20mi**: Destination market to capture long-distance visitors without excessive geographic overlap

The 20-mile radius is critical for modeling because:
1. **~19% of visits travel 30+ miles** - indicating significant destination appeal
2. Captures suburban sprawl and exurban customers in FL/PA markets
3. Better differentiation between urban (reliant on <5mi) vs destination locations (strong 10-20mi draw)
4. Helps model rural locations where customer base is geographically dispersed

**Model Feature Engineering**: We can create derived features like:
- `pop_ratio_1_to_5mi`: (pop_1mi / pop_5mi) - urbanization proxy
- `pop_ratio_5_to_20mi`: (pop_5mi / pop_20mi) - suburban vs rural indicator
- `extended_market_index`: pop_10mi + pop_20mi - destination appeal potential

### Age Distribution Variables (Optional Phase 2.5)

If initial model performance needs improvement, add detailed age breakdowns:

| Variable Code | Description |
|--------------|-------------|
| **B01001_007E - B01001_025E** | Male population by age groups |
| **B01001_031E - B01001_049E** | Female population by age groups |

Calculate:
- `pct_age_21_34`: % population age 21-34 (key cannabis demographic)
- `pct_age_35_64`: % population age 35-64 (established consumers)
- `pct_age_65_plus`: % population age 65+ (medical users)

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Census Data Collection Pipeline               │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
         ┌──────────▼──────────┐    ┌──────────▼──────────┐
         │  Geocoding Module   │    │  ACS Data Module    │
         │                     │    │                     │
         │  - Coordinate→FIPS  │    │  - Tract variables  │
         │  - Batch processing │    │  - Multi-tract query│
         │  - Error handling   │    │  - Rate limiting    │
         └──────────┬──────────┘    └──────────┬──────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Geographic Analysis      │
                    │                           │
                    │  - Buffer generation      │
                    │  - Tract intersection     │
                    │  - Population aggregation │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Feature Engineering      │
                    │                           │
                    │  - Calculate percentages  │
                    │  - Population density     │
                    │  - Multi-radius summaries │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Data Integration         │
                    │                           │
                    │  - Merge with combined    │
                    │  - Validation             │
                    │  - Quality reporting      │
                    └───────────────────────────┘
```

---

## Implementation Components

### 1. Census Tract Identifier (`CensusTractIdentifier`)

**Responsibility**: Convert lat/lon coordinates to census tract FIPS codes

**Key Methods**:
```python
class CensusTractIdentifier:
    def __init__(self):
        self.geocoding_url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
        self.session = requests.Session()  # Connection pooling

    def get_tract_from_coordinates(self, latitude: float, longitude: float) -> dict:
        """Get census tract FIPS code from coordinates.

        Returns:
            dict: {
                'state_fips': str,
                'county_fips': str,
                'tract_fips': str,
                'geoid': str (full FIPS code),
                'tract_name': str
            }
        """

    def batch_identify_tracts(self, df: pd.DataFrame,
                             lat_col='latitude',
                             lon_col='longitude') -> pd.DataFrame:
        """Add census tract identifiers to dispensary dataframe."""
```

**Error Handling**:
- Network timeouts: Retry with exponential backoff (3 attempts)
- Invalid coordinates: Flag row with `census_tract_error: True`
- API unavailable: Log error, continue with next record

**Caching**:
- Cache results to avoid re-querying same coordinates
- Save intermediate results to JSON for crash recovery

---

### 2. ACS Data Collector (`ACSDataCollector`)

**Responsibility**: Fetch demographic variables from ACS 5-Year API

**Key Methods**:
```python
import os

class ACSDataCollector:
    def __init__(self):
        # Retrieve API key from environment variable (NEVER hard-code)
        self.api_key = os.environ.get("CENSUS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CENSUS_API_KEY environment variable not set. "
                "Set it with: export CENSUS_API_KEY=your_key_here"
            )

        self.base_url = "https://api.census.gov/data/2023/acs/acs5"
        self.variables = [
            'B01001_001E',  # Total population
            'B01002_001E',  # Median age
            'B19013_001E',  # Median household income
            'B19301_001E',  # Per capita income
            'B15003_001E',  # Total 25+ for education base
            'B15003_022E',  # Bachelor's
            'B15003_023E',  # Master's
            'B15003_024E',  # Professional
            'B15003_025E'   # Doctorate
        ]

    def get_tract_demographics(self, state_fips: str,
                               county_fips: str,
                               tract_fips: str) -> dict:
        """Fetch demographic variables for a single census tract."""

    def batch_collect_demographics(self, tracts_df: pd.DataFrame) -> pd.DataFrame:
        """Collect demographics for all tracts in dataframe."""
```

**Rate Limiting**:
- Implement 1-second delay between requests (conservative)
- Monitor for 429 (rate limit) responses
- Implement exponential backoff if needed

**Data Quality**:
- Handle null/missing values (-666666666 codes)
- Flag tracts with incomplete data
- Log any anomalies (e.g., median income < $10k or > $500k)

---

### 3. Geographic Analysis Module (`GeographicAnalyzer`)

**Responsibility**: Calculate multi-radius population aggregations with area-weighted precision

**Dependencies**:
- `geopandas`: Spatial operations and buffers
- `shapely`: Geometry creation and intersection
- `pyproj`: Coordinate reference system transformations
- Census tract shapefiles (TIGER/Line files)

**Coordinate Reference System (CRS) Strategy**:

**Critical**: Buffers must use planar (equal-area) projections, not lat/lon degrees!

- **Input**: WGS84 (EPSG:4326) - latitude/longitude
- **Processing CRS**:
  - **Florida**: NAD83(2011) Florida GDL Albers (EPSG:3086) - optimized for FL
  - **Pennsylvania**: NAD83(2011) Pennsylvania Albers (EPSG:6565) - optimized for PA
  - **Alternative**: USA Contiguous Albers Equal Area (EPSG:5070) - works for both states
- **Output**: WGS84 (EPSG:4326) - for consistency with input data
- **Buffer Units**: Miles (convert to meters: miles × 1609.34)

**Why This Matters**:
- Lat/lon buffers create degree-based "circles" that are elliptical and distance-inaccurate
- Small buffers (1mi, 3mi) in sparse counties would drastically overcount population if whole tracts included
- Equal-area projections ensure accurate distance-based buffers

**Area-Weighted Population Calculation**:

**Problem**: Simply counting all tracts that intersect a buffer inflates population estimates, especially for:
- Small radii (1mi, 3mi) in counties with large census tracts
- Rural areas where tracts can be 50+ square miles

**Solution**: Weight each tract's population by the proportion that falls within the buffer:

```
population_in_buffer = tract_population × (intersection_area ÷ tract_total_area)
```

**Example**:
- Census tract has 5,000 people and 10 sq mi total area
- Buffer intersects 2 sq mi of the tract (20%)
- Add 5,000 × (2 ÷ 10) = 1,000 people to buffer total (not all 5,000)

This ensures:
- `pop_1mi ≤ pop_3mi ≤ pop_5mi ≤ pop_10mi ≤ pop_20mi` (monotonic increase)
- Realistic population counts for all buffer sizes
- Accurate handling of partially-intersected tracts

**Key Methods**:
```python
class GeographicAnalyzer:
    def __init__(self):
        # Load census tract boundaries (TIGER/Line shapefiles)
        self.fl_tracts = gpd.read_file('path/to/FL_tracts.shp')
        self.pa_tracts = gpd.read_file('path/to/PA_tracts.shp')

        # Precompute tract areas in original CRS for weighting
        self.fl_tracts['tract_area_sqm'] = self.fl_tracts.to_crs(epsg=3086).geometry.area
        self.pa_tracts['tract_area_sqm'] = self.pa_tracts.to_crs(epsg=6565).geometry.area

        # Define state-specific processing CRS
        self.state_crs = {
            'FL': 'EPSG:3086',  # Florida GDL Albers
            'PA': 'EPSG:6565'   # Pennsylvania Albers
        }

    def create_buffer(self, latitude: float, longitude: float,
                     radius_miles: float, state: str) -> Polygon:
        """Create accurate circular buffer around point.

        Steps:
        1. Create Point in WGS84 (EPSG:4326)
        2. Reproject to state-specific Albers equal-area CRS
        3. Buffer by radius in meters (miles × 1609.34)
        4. Return buffer geometry in processing CRS (NOT reprojected back)

        Args:
            latitude: Dispensary latitude (WGS84)
            longitude: Dispensary longitude (WGS84)
            radius_miles: Buffer radius in miles
            state: 'FL' or 'PA' for CRS selection

        Returns:
            Polygon in state-specific Albers CRS
        """

    def calculate_area_weighted_population(self, buffer: Polygon,
                                          tracts_gdf: gpd.GeoDataFrame,
                                          population_col: str = 'B01001_001E') -> dict:
        """Calculate population using area-weighted intersection.

        Steps:
        1. Find all tracts that intersect the buffer (using spatial index)
        2. For each intersecting tract:
           a. Calculate intersection geometry
           b. Calculate intersection area
           c. Weight population: tract_pop × (intersection_area ÷ tract_area)
        3. Sum weighted populations

        Args:
            buffer: Buffer polygon (in processing CRS, e.g., EPSG:3086)
            tracts_gdf: Census tracts GeoDataFrame (in same CRS as buffer)
            population_col: Column name for population variable

        Returns:
            dict: {
                'total_population': float,
                'tract_count': int,
                'tracts': list[str],  # GEOIDs for debugging
                'weights': dict[str, float]  # GEOID -> area weight for validation
            }
        """

    def calculate_multi_radius_population(self,
                                         latitude: float,
                                         longitude: float,
                                         state: str,
                                         tract_populations: gpd.GeoDataFrame) -> dict:
        """Calculate area-weighted population within 1, 3, 5, 10, and 20 mile radii.

        Based on Insa trade area analysis showing ~19% of visits from 30+ miles,
        we include extended radii to capture destination appeal and suburban sprawl.

        Implementation:
        1. Reproject point from WGS84 to state-specific Albers CRS
        2. Create buffers in planar CRS (accurate distance-based circles)
        3. Calculate area-weighted population for each buffer
        4. Validate monotonic increase (1mi ≤ 3mi ≤ 5mi ≤ 10mi ≤ 20mi)

        Returns:
            dict: {
                'pop_1mi': float,   # Area-weighted population
                'pop_3mi': float,
                'pop_5mi': float,
                'pop_10mi': float,
                'pop_20mi': float,
                'tracts_1mi': list[str],  # For debugging/validation
                'tracts_3mi': list[str],
                'tracts_5mi': list[str],
                'tracts_10mi': list[str],
                'tracts_20mi': list[str],
                'crs_used': str  # Document which CRS was used (e.g., 'EPSG:3086')
            }
        """
```

**Performance Optimization**:
- Spatial indexing (R-tree) for fast tract lookups - only check intersecting tracts
- Pre-load all tract boundaries into memory
- Precompute tract areas to avoid repeated calculations
- Cache buffer calculations if coordinates repeat
- Single projection operation per dispensary (not per radius)

**Edge Cases**:
- **Buffers crossing state boundaries**: Use appropriate CRS for dispensary's state, then check both state tract files if buffer extends beyond boundary
- **Water bodies**: Census tracts include water area, but population reflects land only (correct behavior)
- **Large rural tracts**: Area-weighting solves the over-counting problem automatically
- **Partial intersections**: Geometry intersection area accurately captures fractional coverage

---

### 4. Feature Engineering Module (`CensusFeatureEngineer`)

**Responsibility**: Calculate derived features and prepare data for modeling

**Key Methods**:
```python
class CensusFeatureEngineer:
    def calculate_education_percentage(self, row: pd.Series) -> float:
        """Calculate % population 25+ with bachelor's degree or higher."""
        bachelors_plus = (row['B15003_022E'] + row['B15003_023E'] +
                         row['B15003_024E'] + row['B15003_025E'])
        total_25_plus = row['B15003_001E']
        return (bachelors_plus / total_25_plus * 100) if total_25_plus > 0 else None

    def calculate_population_density(self, population: int,
                                    tract_geoid: str) -> float:
        """Calculate population per square mile using tract area."""

    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all derived census features to dataframe."""
```

---

### 5. Data Integration Module (`CensusDataIntegrator`)

**Responsibility**: Merge census data with combined dispensary datasets

**Key Methods**:
```python
class CensusDataIntegrator:
    def integrate_census_data(self,
                             combined_df: pd.DataFrame,
                             census_df: pd.DataFrame) -> pd.DataFrame:
        """Merge census features into combined dataset."""

    def validate_integration(self, df: pd.DataFrame) -> dict:
        """Validate census data quality and generate report.

        Returns:
            dict: {
                'total_dispensaries': int,
                'census_complete': int,
                'census_partial': int,
                'census_missing': int,
                'pct_complete': float,
                'null_counts': dict,
                'value_ranges': dict
            }
        """

    def generate_summary_report(self, validation_results: dict) -> None:
        """Create JSON summary of census integration quality."""
```

---

## Data Schema Extensions

### New Fields Added to Combined Datasets

**Census Tract Identification**:
- `census_state_fips`: 2-digit state FIPS code (e.g., "12" for FL)
- `census_county_fips`: 3-digit county FIPS code (e.g., "086")
- `census_tract_fips`: 6-digit tract code (e.g., "011702")
- `census_geoid`: Full 11-digit GEOID (state+county+tract)
- `census_tract_name`: Human-readable name (e.g., "Census Tract 117.02")

**Demographic Variables (Tract-Level)**:
- `total_population`: Total population in dispensary's census tract
- `median_age`: Median age in years
- `median_household_income`: Median household income ($)
- `per_capita_income`: Per capita income ($)
- `pct_bachelor_plus`: % population 25+ with bachelor's degree or higher
- `population_density`: People per square mile

**Multi-Radius Population**:
- `pop_1mi`: Total population within 1-mile radius
- `pop_3mi`: Total population within 3-mile radius
- `pop_5mi`: Total population within 5-mile radius
- `pop_10mi`: Total population within 10-mile radius
- `pop_20mi`: Total population within 20-mile radius

**Derived Market Indicators** (Optional for modeling):
- `pop_ratio_1_to_5mi`: Urbanization proxy (higher = more urban)
- `pop_ratio_5_to_20mi`: Suburban sprawl indicator
- `extended_market_potential`: pop_10mi + pop_20mi (destination appeal)

**Data Quality Flags**:
- `census_data_complete`: Boolean - all census variables successfully retrieved
- `census_tract_error`: Boolean - error identifying census tract
- `census_api_error`: Boolean - error retrieving ACS data
- `census_collection_date`: Date census data was collected

---

## File Structure

```
src/
├── feature_engineering/
│   ├── __init__.py
│   ├── census_tract_identifier.py      # CensusTractIdentifier class
│   ├── acs_data_collector.py           # ACSDataCollector class
│   ├── geographic_analyzer.py          # GeographicAnalyzer class
│   ├── census_feature_engineer.py      # CensusFeatureEngineer class
│   ├── census_data_integrator.py       # CensusDataIntegrator class
│   └── collect_census_data.py          # Main orchestration script
│
data/
├── census/
│   ├── tract_shapefiles/               # TIGER/Line tract boundaries
│   │   ├── FL_tracts/
│   │   └── PA_tracts/
│   ├── cache/                          # Cached API responses
│   │   ├── geocoding_cache.json
│   │   └── acs_cache.json
│   └── intermediate/                   # Recovery checkpoints
│       ├── tracts_identified.csv
│       └── demographics_collected.csv
│
tests/
├── test_census_tract_identifier.py
├── test_acs_data_collector.py
├── test_geographic_analyzer.py
├── test_census_feature_engineer.py
└── test_census_data_integrator.py

# Security: Environment Variables and Credentials
.env                                     # NEVER commit (add to .gitignore)
.env.example                             # Template showing required variables
```

### `.env.example` Template:
```bash
# Census Bureau API Key
# Obtain free key at: https://api.census.gov/data/key_signup.html
CENSUS_API_KEY=your_census_api_key_here
```

### `.gitignore` Additions:
```
# Environment variables (contains API keys)
.env
.env.*
*.env

# Cached credentials
data/census/cache/*.json
```

---

## Processing Pipeline

### Step-by-Step Workflow

1. **Load Combined Datasets**
   - Read FL_combined_dataset_current.csv
   - Read PA_combined_dataset_current.csv
   - Filter to `has_placer_data: True` (741 dispensaries)

2. **Identify Census Tracts** (CensusTractIdentifier)
   - For each dispensary with coordinates:
     - Call Geocoding API with lat/lon
     - Extract state, county, tract FIPS codes
     - Save intermediate results every 100 records
   - Generate cache to avoid re-querying on failures

3. **Collect ACS Demographics** (ACSDataCollector)
   - Get unique list of census tracts
   - For each unique tract:
     - Query ACS API for demographic variables
     - Handle missing values and errors
     - Cache results
   - Join demographics back to dispensaries by GEOID

4. **Calculate Multi-Radius Population** (GeographicAnalyzer)
   - Load census tract shapefiles for FL and PA
   - Precompute tract areas in state-specific Albers CRS
   - For each dispensary:
     - Reproject point from WGS84 to state-specific Albers CRS (EPSG:3086 for FL, EPSG:6565 for PA)
     - Create 1, 3, 5, 10, 20-mile buffers in planar CRS (convert miles to meters: × 1609.34)
     - Find all tracts intersecting each buffer (using spatial index)
     - **Area-weighted population**: For each intersecting tract:
       - Calculate intersection geometry
       - Weight population by intersection_area ÷ tract_area
       - Sum weighted populations (not whole-tract counts)
     - Validate monotonic increase: pop_1mi ≤ pop_3mi ≤ ... ≤ pop_20mi
     - Handle edge cases (state boundaries, partial intersections)
   - Note: 20mi radius critical for capturing destination appeal (19% of Insa visits from 30+ mi)
   - Note: Area-weighting prevents small-buffer inflation in sparse counties

5. **Engineer Features** (CensusFeatureEngineer)
   - Calculate `pct_bachelor_plus` from education variables
   - Calculate `population_density` using tract areas
   - Validate ranges and flag anomalies

6. **Integrate with Combined Datasets** (CensusDataIntegrator)
   - Merge census features into original datasets
   - Preserve all original columns
   - Add data quality flags
   - Generate validation report

7. **Quality Validation**
   - Check completion rates (target: >95% of 741 dispensaries)
   - Validate value ranges (income, age, population)
   - Generate summary statistics
   - Create Phase 2 completion report

---

## Error Handling Strategy

### Geocoding Failures
- **Cause**: Invalid coordinates, API timeout, network issues
- **Response**:
  - Retry 3 times with exponential backoff
  - Flag record with `census_tract_error: True`
  - Continue processing, include in final dataset
  - Log all failures to `census_errors.log`

### ACS API Failures
- **Cause**: Rate limiting, API downtime, invalid tract code
- **Response**:
  - Implement 1-second delay between requests
  - Retry with exponential backoff
  - Flag record with `census_api_error: True`
  - Cache partial results for crash recovery

### Missing Values
- **Cause**: Census suppression (small populations), data not available
- **Response**:
  - Preserve null values (don't fill with zeros or estimates)
  - Set `census_data_complete: False`
  - Document in quality report
  - Consider tract-level imputation only if >95% complete

### Geographic Edge Cases
- **Cause**: Buffers crossing state lines, large rural tracts
- **Response**:
  - Load both state tract files when near boundary
  - Use spatial intersection (not just centroids)
  - Log any tracts that couldn't be matched

---

## Testing Strategy

### Unit Tests

**test_census_tract_identifier.py**:
- Valid FL coordinates → correct GEOID
- Valid PA coordinates → correct GEOID
- Invalid coordinates → proper error handling
- API timeout → retry logic works
- Batch processing → all records processed

**test_acs_data_collector.py**:
- Valid tract → all variables returned
- Missing variable → null handling
- API rate limit → backoff works
- Batch collection → caching works

**test_geographic_analyzer.py**:
- CRS transformation → WGS84 to Albers correctly
- 1-mile buffer in Albers → accurate circular buffer (not elliptical)
- 20-mile buffer → handles large geographic area correctly
- Area-weighted population → partial tract intersection calculated correctly
- Buffer crossing state line → both states queried
- Population aggregation → area-weighted sum (not whole-tract counts)
- Edge of state → boundary handling
- Nested buffer validation → pop_1mi ≤ pop_3mi ≤ pop_5mi ≤ pop_10mi ≤ pop_20mi (monotonic)
- Sparse county test → 1mi buffer doesn't overcount population in large rural tract

**test_census_feature_engineer.py**:
- Education percentage calculation
- Population density calculation
- Null value handling
- Derived feature validation

**test_census_data_integrator.py**:
- Merge preserves all original columns
- Data quality flags set correctly
- Validation report accuracy

### Integration Tests

**End-to-End Pipeline**:
- Sample of 10 FL and 10 PA dispensaries
- Run full pipeline
- Validate all features present
- Check data quality flags

---

## Dependencies

### New Requirements (Add to requirements.txt)

```python
# Geospatial analysis
geopandas>=0.14.0,<1.0.0
shapely>=2.0.0,<3.0.0
pyproj>=3.6.0,<4.0.0

# HTTP requests
requests>=2.31.0,<3.0.0

# Census tract shapefiles
pygris>=0.2.0,<1.0.0  # Automatically downloads TIGER/Line files
```

### External Data Dependencies

**Census TIGER/Line Shapefiles** (2023):
- Florida census tracts: Auto-download via pygris
- Pennsylvania census tracts: Auto-download via pygris
- Includes tract boundaries and area calculations

---

## Performance Estimates

### Processing Time

**741 Dispensaries**:
- Geocoding (1 req/sec with caching): ~10-15 minutes
- Unique tracts (~600 estimated): ACS queries (~1 req/sec): ~10 minutes
- Multi-radius calculations with 5 radii (local): ~8-10 minutes (increased from ~5 due to 20mi buffers)
- Feature engineering: ~2 minutes
- Integration and validation: ~3 minutes

**Total Estimated Time**: ~35-45 minutes (first run), ~12-15 minutes (with caching)

**Performance Note**: The 20-mile radius will increase buffer calculation time slightly, but the insights gained about destination appeal justify the ~3-5 minute overhead.

### API Usage

- **Geocoding API**: ~741 requests (one per dispensary)
- **ACS API**: ~600 requests (one per unique tract, not affected by radius count)
- **Total**: ~1,341 API calls

Both APIs are free and should handle this volume without issues. The 20mi radius only affects local geometric calculations, not API usage.

---

## Success Criteria

- ✅ Census tracts identified for >95% of 741 training dispensaries
- ✅ Demographic variables collected for all identified tracts
- ✅ Multi-radius population calculated for all dispensaries
- ✅ No synthetic or estimated data (all real Census Bureau data)
- ✅ Data quality validation shows <5% missing values
- ✅ All changes committed to Git with clear documentation
- ✅ Comprehensive test coverage for all modules

---

## Next Steps After Design Approval

1. **Set Up Census API Access**
   - ✅ API key obtained (store in environment variable)
   - Create `.env` file with `CENSUS_API_KEY=your_key_here`
   - Add `.env` to `.gitignore` (NEVER commit credentials)
   - Create `.env.example` template for documentation
   - Test geocoding and ACS endpoints with sample data
   - Verify 2023 ACS 5-Year data availability

2. **Download Tract Shapefiles**
   - Use pygris to download FL and PA tract boundaries
   - Validate spatial data loads correctly

3. **Implement Core Modules**
   - Build CensusTractIdentifier first (foundational)
   - Then ACSDataCollector
   - Then GeographicAnalyzer (most complex)
   - Finally feature engineering and integration

4. **Test on Sample**
   - Run pipeline on 20 dispensaries (10 FL, 10 PA)
   - Validate results manually
   - Refine error handling

5. **Production Run**
   - Process all 741 training dispensaries
   - Generate comprehensive quality report
   - Update combined datasets

6. **Documentation**
   - Create Phase 2 completion report
   - Document census data methodology
   - Create data dictionary for new variables

---

---

## Revision History

### v1.2 - October 22, 2025 (Codex Review Fixes)
- **CRITICAL: Area-weighted population calculation** - prevents small-buffer inflation in sparse counties
  - Weight each tract by intersection_area ÷ tract_area before summing
  - Ensures monotonic increase: pop_1mi ≤ pop_3mi ≤ ... ≤ pop_20mi
  - Eliminates rural over-counting (e.g., 1mi buffer including entire 50 sq mi tract)
- **CRITICAL: Proper CRS handling** - accurate distance-based buffers
  - Reproject to state-specific Albers equal-area CRS before buffering
  - FL: EPSG:3086 (Florida GDL Albers), PA: EPSG:6565 (Pennsylvania Albers)
  - Convert radius from miles to meters (× 1609.34)
  - Prevents elliptical "circles" from lat/lon degree-based buffers
- **CRITICAL: Credential security** - API key handling
  - Moved API key to environment variable `CENSUS_API_KEY`
  - Added `.env` file pattern and `.gitignore` requirements
  - Created `.env.example` template for documentation
  - Updated `ACSDataCollector.__init__()` to use `os.environ.get()`
- Enhanced testing strategy for CRS transformations and area-weighting
- Updated performance estimates for geometric operations

### v1.1 - October 22, 2025 (Multi-Radius Extension)
- **Added 20-mile radius** based on Insa Jacksonville trade area analysis
- Added multi-radius strategy rationale section
- Documented trade area distribution showing 19% of visits from 30+ miles
- Added derived market indicators (urbanization proxy, destination appeal)
- Updated performance estimates for 5-radius calculations
- Enhanced testing strategy to validate nested buffer logic

### v1.0 - October 22, 2025 (Initial)
- Initial architecture design with 4-radius approach (1, 3, 5, 10 miles)
- Core module specifications and data schema
- API endpoint identification and requirements

---

*Architecture Document v1.1*
*Multi-State Dispensary Prediction Model - Phase 2*
*October 22, 2025*
