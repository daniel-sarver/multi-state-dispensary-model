# Phase 3 Continuation Prompt: Model Development

**Date**: October 23, 2025
**Current Phase**: Phase 3 - Model Development (Ready to Start)
**Previous Phase**: Phase 2 - Census Demographics Integration (✅ COMPLETE)
**GitHub Commit**: d4cf477

---

## Project Status Overview

**Multi-State Dispensary Prediction Model** - Enhanced site analysis for Pennsylvania and Florida

### Phase Completion Status
- ✅ **Phase 1**: Data Integration - 741 training dispensaries, 937 total (with competitive landscape)
- ✅ **Phase 2**: Census Demographics Integration - 100% complete, 24 new features added
- 🚧 **Phase 3**: Model Development - **READY TO START**
- ⏳ **Phase 4**: Interface & Reporting - Planned

---

## Phase 2 Completion Summary

### What Was Accomplished

**Production census data collection completed successfully**:
- **741/741 training dispensaries** (100%) with complete census demographics
- **7,730 unique census tracts** processed across Florida (4,850) and Pennsylvania (2,880)
- **99.96% data completeness** (only 3 tracts with standard ACS suppressions)
- **24 new census features** added to combined datasets
- **Processing time**: ~55 minutes with partial cache

### Critical Technical Achievements

1. **Area-Weighted Population Calculation**:
   - Formula: `population_in_buffer = Σ(tract_pop × intersection_area / tract_area)`
   - Prevents over-counting in rural areas with large sparse census tracts
   - Ensures monotonic increase: pop_1mi ≤ pop_3mi ≤ ... ≤ pop_20mi
   - **Validation**: 100% of dispensaries pass monotonic check

2. **State-Specific CRS Projections**:
   - Florida: EPSG:3086 (Florida GDL Albers equal-area)
   - Pennsylvania: EPSG:6565 (Pennsylvania Albers equal-area)
   - Ensures accurate circular buffers (not elliptical)

3. **Multi-Radius Population Analysis**:
   - 5 buffer zones: 1, 3, 5, 10, 20 miles
   - Realistic growth patterns: urban 100-150x, suburban 50-80x, rural 40-60x
   - Example: Trulieve Orlando shows 12K @ 1mi → 1.78M @ 20mi (143.8x)

---

## Current Dataset Structure

### Training Dispensaries: 741 Total

**Florida**: 590 training dispensaries
**Pennsylvania**: 151 training dispensaries

### Total Dispensaries: 937 (Including Competitive Landscape)

**Florida**: 735 total (590 training + 145 regulator-only)
**Pennsylvania**: 202 total (151 training + 51 regulator-only)

**Important**: Census data was ONLY collected for training dispensaries (`has_placer_data == True`)

---

## New Census Features Available (24 Columns)

### Census Tract Identification (5)
- `census_state_fips`: 2-digit state FIPS
- `census_county_fips`: 3-digit county FIPS
- `census_tract_fips`: 6-digit tract FIPS
- `census_geoid`: 11-digit full GEOID
- `census_tract_name`: Human-readable name

### Home Tract Demographics (9)
- `total_population`: Total population in home tract
- `median_age`: Median age (years)
- `median_household_income`: Median HH income ($)
- `per_capita_income`: Per capita income ($)
- `total_pop_25_plus`: Population 25+ (education base)
- `bachelors_degree`: Count with bachelor's
- `masters_degree`: Count with master's
- `professional_degree`: Count with professional degree
- `doctorate_degree`: Count with doctorate

### Multi-Radius Populations (5)
- `pop_1mi`: Area-weighted population within 1 mile
- `pop_3mi`: Area-weighted population within 3 miles
- `pop_5mi`: Area-weighted population within 5 miles
- `pop_10mi`: Area-weighted population within 10 miles
- `pop_20mi`: Area-weighted population within 20 miles

### Derived Features (2)
- `pct_bachelor_plus`: % population 25+ with bachelor's+
- `population_density`: People per square mile

### Data Quality Flags (3)
- `census_tract_error`: Boolean - geocoding failed
- `census_data_complete`: Boolean - all ACS variables present
- `census_api_error`: Boolean - ACS API failed
- `census_collection_date`: Date collected

---

## Data Quality Notes - CRITICAL FOR MODELING

### Incomplete Census Tracts (3 of 7,730 = 0.04%)

All 3 incomplete tracts are **only in multi-radius buffers, NOT home tracts**:

1. **Philadelphia 42101980300**: Zero-population institutional tract
2. **Philadelphia 42101980701**: Zero-population institutional tract
3. **Florida 12073000502**: Low-population tract with ACS income suppression

**Impact on Training Data**: **ZERO** - all 741 training dispensaries have complete home tract data

### NaN Distribution in Datasets

Census columns show ~20% NaNs overall:
- **Training dispensaries**: 0% NaNs (100% complete)
- **Regulator-only dispensaries**: 100% NaNs (expected - no census data collected)

**Florida**: 145/735 NaNs (19.7%) = all regulator-only entries
**Pennsylvania**: 51/202 NaNs (25.2%) = all regulator-only entries

### Required Filtering for Model Training

**ALWAYS filter to training dispensaries**:
```python
# Recommended approach
training_df = df[df['has_placer_data'] == True]

# Alternative (excludes 1 FL with suppressed median_household_income)
training_df = df[df['census_data_complete'] == True]
```

---

## Phase 3 Goals & Targets

### Primary Objective

**Build enhanced prediction model with significantly improved performance over PA baseline**

### Performance Targets

- **Primary**: R² > 0.15 (major improvement over PA model's 0.0716)
- **Secondary**: RMSE reduction vs PA baseline
- **Validation**: Strong correlation with Insa actual performance data
- **Confidence**: Proper uncertainty quantification for business decisions

### Key Advantages Over PA Model

1. **4.9x larger training set**: 741 vs ~150 dispensaries
2. **Multi-radius populations**: 5 buffer zones vs limited geographic data
3. **Enhanced demographics**: Education, income, density at tract level
4. **State diversity**: Cross-state patterns and universal success factors
5. **Area-weighted calculations**: Mathematically correct population estimates

---

## Recommended Phase 3 Architecture

### Step 1: Enhanced Feature Engineering

**Module**: `src/feature_engineering/competitive_features.py`

**Features to Create**:

1. **Multi-Radius Competition**:
   - Competitor count within 1, 3, 5, 10, 20 miles
   - Distance-weighted competition scores
   - Market saturation (dispensaries per capita at each radius)

2. **Demographic Interactions**:
   - `pop_5mi × median_household_income` (affluent market size)
   - `pct_bachelor_plus × population_density` (educated urban markets)
   - `median_age × pop_3mi` (age-adjusted catchment)

3. **State-Specific Factors**:
   - Florida vs Pennsylvania indicator
   - State × population interaction terms
   - State × competition density interactions

4. **Accessibility Metrics** (if data available):
   - AADT (Annual Average Daily Traffic) where available
   - Highway access indicators
   - Urban/suburban/rural classification

### Step 2: Model Development

**Module**: `src/modeling/train_multi_state_model.py`

**Modeling Approach**:

1. **Enhanced Ridge Regression** (baseline):
   - State interaction terms
   - Regularization strength tuning
   - Feature scaling/normalization

2. **Ensemble Methods** (if Ridge insufficient):
   - Random Forest (handles non-linearity)
   - XGBoost (gradient boosting)
   - Model stacking

3. **Cross-Validation Strategy**:
   - Geographic CV with state-based splits
   - Leave-one-state-out validation
   - K-fold CV within states

4. **Feature Selection**:
   - Recursive feature elimination
   - Feature importance analysis
   - Variance inflation factor (multicollinearity check)

### Step 3: Model Validation

**Module**: `src/modeling/validate_model.py`

**Validation Approach**:

1. **Performance Metrics**:
   - R² (coefficient of determination)
   - RMSE (root mean squared error)
   - MAE (mean absolute error)
   - MAPE (mean absolute percentage error)

2. **Residual Analysis**:
   - Residual plots by state
   - QQ plots for normality
   - Heteroscedasticity checks
   - Outlier identification

3. **Insa Benchmark Validation**:
   - Compare predictions to actual Insa store performance
   - Florida, Massachusetts, Connecticut stores
   - Calculate prediction accuracy on Insa sites

4. **Confidence Intervals**:
   - Bootstrap confidence intervals
   - Prediction intervals for new sites
   - Uncertainty quantification

### Step 4: Terminal Interface & Reporting

**Module**: `src/reporting/terminal_interface.py`

**Interface Features** (adapting from PA model v3.1):

1. **Multi-State Predictions**:
   - Select state (FL or PA)
   - Input site characteristics
   - Generate visit predictions with confidence intervals

2. **Scenario Analysis**:
   - What-if analysis for different locations
   - Population sensitivity analysis
   - Competition impact assessment

3. **Risk Assessment**:
   - Prediction confidence levels
   - Market saturation warnings
   - Competitive pressure indicators

4. **Reporting Output**:
   - Clean terminal formatting
   - CSV export capabilities
   - Summary statistics and rankings

---

## Data File Locations

### Combined Datasets (with Census Features)

**Florida**:
- `data/processed/FL_combined_dataset_current.csv`
- 735 rows (590 training + 145 regulator-only)
- 57 columns (22 original + 35 census)

**Pennsylvania**:
- `data/processed/PA_combined_dataset_current.csv`
- 202 rows (151 training + 51 regulator-only)
- 64 columns (29 original + 35 census)

### Census Integration Reports

**Florida**: `data/census/FL_census_integration_report.json`
**Pennsylvania**: `data/census/PA_census_integration_report.json`

### Checkpoint Files (for reference)

- `data/census/intermediate/features_engineered.csv` (741 rows, all census features)
- `data/census/intermediate/demographics_collected.csv` (7,730 tracts)

---

## Key Code Modules Available

### Phase 2 Census Collection (Complete)
- `src/feature_engineering/census_tract_identifier.py`
- `src/feature_engineering/acs_data_collector.py`
- `src/feature_engineering/geographic_analyzer.py`
- `src/feature_engineering/census_feature_engineer.py`
- `src/feature_engineering/census_data_integrator.py`
- `src/feature_engineering/collect_census_data.py` (orchestration)

### Phase 1 Data Integration (Complete)
- `src/data_integration/` (Placer + Regulator merging)

### Phase 3 Modules (To Be Created)
- `src/feature_engineering/competitive_features.py` (NEW)
- `src/modeling/train_multi_state_model.py` (NEW)
- `src/modeling/validate_model.py` (NEW)
- `src/reporting/terminal_interface.py` (NEW)

---

## Important Implementation Notes

### Data Integrity Principles (HIGHEST PRIORITY)

1. **NEVER USE SYNTHETIC DATA** without explicit approval
2. **ALWAYS filter to training dispensaries** for modeling: `df[df['has_placer_data'] == True]`
3. **Validate coordinates** are within state boundaries
4. **Handle NaNs explicitly** - document all imputation strategies
5. **Document all transformations** for reproducibility

### Modeling Best Practices

1. **Start simple, add complexity incrementally**:
   - Begin with basic Ridge regression
   - Add state interactions
   - Test ensemble methods if needed

2. **Cross-validation strategy**:
   - Use geographic CV (state-based splits)
   - Prevent data leakage across states
   - Validate on Insa actual performance

3. **Feature engineering discipline**:
   - Document all new features created
   - Check for multicollinearity (VIF < 10)
   - Feature importance analysis

4. **Testing before production**:
   - Unit tests for feature engineering
   - Integration tests for full pipeline
   - Validation on hold-out test set

### Git & Documentation Standards

1. **Frequent commits** with descriptive messages
2. **Feature branches** for major development work
3. **Never commit** raw data files (use .gitignore)
4. **Document methodology** in markdown files

---

## Expected Phase 3 Deliverables

### Code Deliverables
1. Enhanced feature engineering module (competitive metrics)
2. Model training pipeline with cross-validation
3. Model validation suite with performance metrics
4. Terminal interface for predictions
5. Comprehensive test suite

### Documentation Deliverables
1. `PHASE3_ARCHITECTURE.md` - Technical design
2. `PHASE3_FEATURE_ENGINEERING.md` - New features created
3. `PHASE3_MODEL_PERFORMANCE.md` - Results and validation
4. `PHASE3_COMPLETION_REPORT.md` - Final summary
5. Updated README.md with Phase 3 status

### Model Artifacts
1. Trained model file(s) in `data/models/`
2. Feature importance analysis
3. Performance metrics on test set
4. Validation results vs Insa benchmarks

---

## Quick Start for Phase 3

```bash
# Navigate to project directory
cd /Users/daniel_insa/Claude/multi-state-dispensary-model

# Confirm datasets are ready
ls -lh data/processed/FL_combined_dataset_current.csv
ls -lh data/processed/PA_combined_dataset_current.csv

# Create Phase 3 modules directory
mkdir -p src/modeling

# Load data and confirm training subset
python3 -c "
import pandas as pd
fl = pd.read_csv('data/processed/FL_combined_dataset_current.csv')
pa = pd.read_csv('data/processed/PA_combined_dataset_current.csv')
print(f'FL training: {fl[fl.has_placer_data==True].shape[0]}/735')
print(f'PA training: {pa[pa.has_placer_data==True].shape[0]}/202')
print(f'Total training: {fl[fl.has_placer_data==True].shape[0] + pa[pa.has_placer_data==True].shape[0]}')
"
```

**Expected Output**:
```
FL training: 590/735
PA training: 151/202
Total training: 741
```

---

## Documentation References

### Phase 2 Documentation (Complete)
- **[PHASE2_COMPLETION_REPORT.md](PHASE2_COMPLETION_REPORT.md)** - Production run summary
- **[PHASE2_DATA_QUALITY_NOTES.md](PHASE2_DATA_QUALITY_NOTES.md)** - Data quality analysis
- **[PHASE2_ARCHITECTURE.md](PHASE2_ARCHITECTURE.md)** - Census integration architecture (v1.2)
- **[PHASE2_IMPLEMENTATION_COMPLETE.md](PHASE2_IMPLEMENTATION_COMPLETE.md)** - Implementation details

### Phase 1 Documentation (Complete)
- **[PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md)** - Data integration summary

### Project Guidelines
- **[CLAUDE.md](../CLAUDE.md)** - Project principles and standards
- **[README.md](../README.md)** - Project overview and status

---

## Key Questions to Address in Phase 3

### Feature Engineering
1. Which radius (1, 3, 5, 10, 20 mi) performs best for population features?
2. How should competition be weighted by distance?
3. What demographic interactions are most predictive?
4. Should state be modeled as fixed effect or random effect?

### Model Selection
1. Does Ridge regression achieve R² > 0.15 target?
2. Are ensemble methods (RF, XGBoost) necessary?
3. How much improvement from PA baseline (0.0716)?
4. What's the optimal regularization strength?

### Validation
1. How well do predictions match Insa actual stores?
2. Are errors consistent across states?
3. What's the prediction confidence interval width?
4. Which features drive the strongest predictions?

---

## Success Criteria for Phase 3

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| **Primary Performance** | R² > 0.15 | Cross-validated R² on test set |
| **Baseline Improvement** | 2x improvement | R² ratio vs PA model (0.0716) |
| **RMSE Reduction** | <50% of mean visits | Normalized RMSE on test set |
| **Insa Validation** | High correlation | R² on Insa actual stores |
| **Confidence Intervals** | <±30% width | Prediction interval width |
| **Feature Importance** | Clear drivers | Top 5 features identified |
| **Cross-State Validity** | Consistent errors | Similar RMSE in FL and PA |

---

## Context for AI Assistant

**You are resuming work on Phase 3 (Model Development) of the Multi-State Dispensary Prediction Model project.**

**What was just completed**:
- Phase 2 Census Demographics Integration finished successfully
- 741 training dispensaries with 24 new census features
- 99.96% data completeness achieved
- All documentation updated and committed to GitHub (commit d4cf477)

**What to do next**:
1. Review Phase 2 completion documentation if needed
2. Design Phase 3 architecture (feature engineering + modeling)
3. Begin implementation of competitive features module
4. Build model training pipeline with cross-validation
5. Target: R² > 0.15 (major improvement over 0.0716 baseline)

**Critical reminders**:
- ALWAYS filter to training data: `df[df['has_placer_data'] == True]`
- No synthetic data without explicit approval
- Document all methodology decisions
- Start simple (Ridge) before complex models
- Validate against Insa actual performance

**Expected timeline**: Phase 3 is a major development effort, likely 3-5 days of focused work.

---

*Multi-State Dispensary Model - Phase 3 Continuation Prompt*
*Created: October 23, 2025*
*Last Phase Commit: d4cf477*
*Ready to begin: Model Development*
