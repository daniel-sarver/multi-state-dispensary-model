# Phase 2 Implementation Prompt - Census Demographics Integration

**Use this prompt after compacting the chat to begin Phase 2 implementation**

---

I'd like to resume work on my Multi-State Dispensary Model project.

We've completed **Phase 1 (Data Integration)** and **Phase 2 Architecture Design**. I'm now ready to begin **Phase 2 Implementation: Census Demographics Integration**.

## Phase 2 Architecture - Ready for Implementation ✅

We have a complete, production-ready architecture (v1.2) that has been:
- ✅ Designed with Census Bureau API integration strategy
- ✅ Reviewed and enhanced by Codex (critical fixes applied)
- ✅ Documented with comprehensive technical specifications

Please review the architecture document at:
**`/Users/daniel_insa/Claude/multi-state-dispensary-model/docs/PHASE2_ARCHITECTURE.md`**

## What's Been Completed

### Phase 1: Data Integration ✅ COMPLETE

**Deliverables**:
- **741 training-eligible dispensaries** across PA & FL (98.8% of 750 target)
- **937 total dispensaries** for competitive landscape
- Production-ready combined datasets:
  - `/data/processed/FL_combined_dataset_current.csv` (735 dispensaries)
  - `/data/processed/PA_combined_dataset_current.csv` (202 dispensaries)

**Data Quality**:
- 100% coordinate coverage for training dispensaries
- 100% visit data coverage for training set
- 96-98 average match confidence scores
- Enhanced cannabis-only filtering with brand whitelist
- Comprehensive test suite for regression prevention

**Key Documents**:
- `/docs/PHASE1_COMPLETION_REPORT.md` - Complete Phase 1 summary
- `/docs/CODE_REVIEW_FIXES.md` - Enhanced matching algorithms (+98 dispensaries)

---

### Phase 2: Architecture Design ✅ COMPLETE

**Architecture Version**: v1.2 (production-ready after Codex review)

**Key Design Decisions**:

1. **Area-Weighted Population Calculation** (Critical Fix from Codex)
   - Prevents small-buffer inflation in sparse counties
   - Formula: `population_in_buffer = tract_pop × (intersection_area ÷ tract_area)`
   - Ensures monotonic increase: `pop_1mi ≤ pop_3mi ≤ ... ≤ pop_20mi`

2. **Proper CRS Handling** (Critical Fix from Codex)
   - State-specific Albers equal-area projections
   - Florida: EPSG:3086 (Florida GDL Albers)
   - Pennsylvania: EPSG:6565 (Pennsylvania Albers)
   - Prevents elliptical buffers from lat/lon degree-based calculations

3. **Multi-Radius Strategy** (Based on Insa Trade Area Data)
   - **1 mile**: Immediate local market
   - **3 miles**: Core trade area
   - **5 miles**: Extended local market
   - **10 miles**: Regional market
   - **20 miles**: Destination market (captures 19% of visits from 30+ miles)

4. **Secure Credential Management** (Critical Fix from Codex)
   - Census API key stored in environment variable: `CENSUS_API_KEY`
   - Never committed to Git (`.env` in `.gitignore`)
   - Template provided: `.env.example`

**Architecture Components** (5 Modules):
1. `CensusTractIdentifier` - Coordinate → FIPS conversion
2. `ACSDataCollector` - Demographic data retrieval
3. `GeographicAnalyzer` - Multi-radius population with area-weighting
4. `CensusFeatureEngineer` - Derived feature calculations
5. `CensusDataIntegrator` - Merge with combined datasets

**Key Documents**:
- `/docs/PHASE2_ARCHITECTURE.md` - Complete technical architecture (v1.2)
- `/docs/CODEX_REVIEW_PHASE2.md` - Critical architecture fixes documentation

---

## Phase 2 Implementation - What We Need to Build

### Objective
Add demographic features to all **741 training-eligible dispensaries** to enhance model predictive power.

### Required Demographic Features

**Core Census Variables** (ACS 5-Year 2023):
- Total Population (B01001_001E)
- Median Age (B01002_001E)
- Median Household Income (B19013_001E)
- Per Capita Income (B19301_001E)
- Education: Bachelor's+ (B15003_022E through B15003_025E)

**Multi-Radius Population**:
- `pop_1mi`, `pop_3mi`, `pop_5mi`, `pop_10mi`, `pop_20mi`
- Calculated using area-weighted intersection (NOT whole-tract counts)

**Derived Features**:
- `pct_bachelor_plus` - % population 25+ with bachelor's degree or higher
- `population_density` - People per square mile

### Implementation Steps

**Step 1: Environment Setup**
- Create `.env` file with Census API key (I'll provide)
- Install new dependencies: `geopandas`, `shapely`, `pyproj`, `pygris`, `requests`
- Update `requirements.txt`

**Step 2: Build Core Modules** (in order)
1. **CensusTractIdentifier** (`src/feature_engineering/census_tract_identifier.py`)
   - Convert lat/lon to census tract FIPS codes
   - Use Census Geocoding API (no key required)
   - Implement caching and error handling

2. **ACSDataCollector** (`src/feature_engineering/acs_data_collector.py`)
   - Fetch demographic variables from ACS 5-Year API
   - Use `os.environ.get("CENSUS_API_KEY")`
   - Implement rate limiting and caching

3. **GeographicAnalyzer** (`src/feature_engineering/geographic_analyzer.py`)
   - **CRITICAL**: Implement area-weighted population calculation
   - **CRITICAL**: Use state-specific Albers projections for buffers
   - Calculate population for 1, 3, 5, 10, 20-mile radii
   - Download tract shapefiles via `pygris`

4. **CensusFeatureEngineer** (`src/feature_engineering/census_feature_engineer.py`)
   - Calculate `pct_bachelor_plus` from education variables
   - Calculate `population_density` using tract areas
   - Validate value ranges

5. **CensusDataIntegrator** (`src/feature_engineering/census_data_integrator.py`)
   - Merge census features with combined datasets
   - Preserve all original columns
   - Add data quality flags
   - Generate validation report

**Step 3: Orchestration Script**
- Create `src/feature_engineering/collect_census_data.py`
- Run all modules in sequence
- Generate comprehensive progress logging
- Save intermediate checkpoints for crash recovery

**Step 4: Testing**
- Write unit tests for each module
- Test on sample (10 FL, 10 PA dispensaries)
- Validate area-weighting prevents over-counting
- Validate CRS transformations
- Check monotonic population increase

**Step 5: Production Run**
- Process all 741 training dispensaries
- Generate quality report
- Update combined datasets with census features

### Census API Configuration

**API Key**: I have a Census Bureau API key ready to provide
- Store in `.env` file as: `CENSUS_API_KEY=your_key_here`
- **NEVER commit to Git** (already in `.gitignore`)

**APIs Used**:
1. **Geocoding API** (no key required):
   - Endpoint: `https://geocoding.geo.census.gov/geocoder/geographies/coordinates`
   - Purpose: lat/lon → census tract FIPS code

2. **ACS 5-Year API** (requires key):
   - Endpoint: `https://api.census.gov/data/2023/acs/acs5`
   - Purpose: Demographic variables by tract

### Expected Performance

**Processing Time**:
- Geocoding: ~10-15 minutes (741 dispensaries, with caching)
- ACS demographics: ~10 minutes (~600 unique tracts)
- Multi-radius calculations: ~8-10 minutes (area-weighted, 5 radii)
- Feature engineering: ~2 minutes
- Integration: ~3 minutes

**Total**: ~35-45 minutes first run, ~12-15 minutes with caching

### Success Criteria

- ✅ Census tracts identified for >95% of 741 training dispensaries
- ✅ Demographic variables collected for all identified tracts
- ✅ Multi-radius population calculated with area-weighting
- ✅ Monotonic population increase validated (1mi ≤ 3mi ≤ ... ≤ 20mi)
- ✅ No synthetic or estimated data (all real Census Bureau data)
- ✅ Data quality validation shows <5% missing values
- ✅ All changes committed to Git with clear messages
- ✅ Comprehensive test coverage

---

## Important Reminders

### Data Integrity (HIGHEST PRIORITY)
- **NEVER use synthetic data** - All census data must come from Census Bureau API
- **ALWAYS use verified real data** from legitimate sources
- If real data unavailable, flag clearly - don't fabricate
- Document all data sources and transformations

### Critical Technical Requirements

**Area-Weighting** (from Codex review):
- DO NOT count whole tracts inside buffers
- MUST weight by intersection area: `tract_pop × (intersection_area ÷ tract_area)`
- Example: 1mi buffer (3 sq mi) intersects 50 sq mi tract with 5,000 people
  - ❌ Wrong: Count all 5,000 people
  - ✅ Correct: 5,000 × (3 ÷ 50) = 300 people

**CRS Handling** (from Codex review):
- DO NOT buffer in lat/lon degrees (creates ellipses, not circles)
- MUST reproject to Albers before buffering
- Florida: Use EPSG:3086
- Pennsylvania: Use EPSG:6565
- Convert miles to meters: `radius_miles × 1609.34`

**Credential Security** (from Codex review):
- NEVER hard-code API keys
- ALWAYS use `os.environ.get("CENSUS_API_KEY")`
- Verify `.env` is in `.gitignore`

### Code Quality Standards
- Follow existing patterns from Phase 1 (`src/data_integration/`)
- Comprehensive logging and progress tracking
- Error handling with retry logic
- Intermediate checkpoints for crash recovery
- Clear, descriptive variable names (snake_case)

### Git Workflow
- Frequent commits with descriptive messages
- Test code before committing
- Push regularly to remote repository
- Document significant changes in commit messages

---

## Files to Reference

**Phase 1 Code** (patterns to follow):
- `/src/data_integration/create_combined_datasets.py` - Reference for code style
- `/tests/test_data_integration.py` - Testing patterns

**Phase 2 Architecture**:
- `/docs/PHASE2_ARCHITECTURE.md` - Complete technical specifications (v1.2)
- `/docs/CODEX_REVIEW_PHASE2.md` - Critical fixes and rationale

**Project Guidelines**:
- `/CLAUDE.md` - Project principles and standards
- `/requirements.txt` - Current dependencies (needs updates)

**Combined Datasets** (input data):
- `/data/processed/FL_combined_dataset_current.csv` - 735 FL dispensaries
- `/data/processed/PA_combined_dataset_current.csv` - 202 PA dispensaries

**Environment Setup**:
- `/.env.example` - Template for environment variables

---

## Next Steps

After reviewing the architecture, let's:

1. **Set up environment**:
   - Create `.env` file with Census API key
   - Update `requirements.txt` with new dependencies
   - Verify `.gitignore` protects credentials

2. **Build CensusTractIdentifier first**:
   - Test with sample coordinates (2-3 FL, 2-3 PA)
   - Validate FIPS codes are correct
   - Implement caching

3. **Proceed sequentially through modules**:
   - Test each module independently before integration
   - Start with small samples before processing all 741

4. **Comprehensive validation**:
   - Verify area-weighting works correctly
   - Check CRS transformations
   - Validate monotonic population increase

---

## Ready to Begin!

Please review:
1. `/docs/PHASE2_ARCHITECTURE.md` - Complete technical specifications
2. `/docs/CODEX_REVIEW_PHASE2.md` - Critical architecture fixes

Then let's start implementing the `CensusTractIdentifier` module!

**Census API Key**: I'll provide this when we start implementation.

Let me know when you've reviewed the architecture and are ready to build the first module.

---

*Project: Multi-State Dispensary Prediction Model*
*Current Phase: Phase 2 Implementation - Census Demographics Integration*
*GitHub: https://github.com/daniel-sarver/multi-state-dispensary-model*
*Date: October 22, 2025*
