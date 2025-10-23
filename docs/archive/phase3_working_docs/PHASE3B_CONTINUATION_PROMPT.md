# Phase 3b Continuation Prompt: Model Training & Validation

**Date**: October 23, 2025
**Current Phase**: Phase 3b - Model Training & Validation (Ready to Start)
**Previous Phase**: Phase 3a - Competitive Features Engineering (✅ COMPLETE)
**GitHub Commit**: 1bf91bc

---

## Project Status Overview

**Multi-State Dispensary Prediction Model** - Enhanced site analysis for Pennsylvania and Florida

### Phase Completion Status
- ✅ **Phase 1**: Data Integration - 741 training dispensaries, 937 total
- ✅ **Phase 2**: Census Demographics - 24 census features, 99.6% complete
- ✅ **Phase 3a**: Competitive Features - 14 competitive features, 100% complete
- 🚧 **Phase 3b**: Model Training - **READY TO START**
- ⏳ **Phase 3c**: Terminal Interface - Planned
- ⏳ **Phase 4**: Documentation & Deployment - Planned

---

## Phase 3a Completion Summary

### What Was Accomplished

**Competitive feature engineering completed successfully**:
- **14 new competitive features** created with 100% completeness
- **741/741 training dispensaries** with complete competitive metrics
- **16 seconds** total processing time for full dataset
- **State files synchronized** with automatic backups
- **Code review issues** all addressed

### Competitive Features Available (14 Total)

1. **Multi-Radius Competitor Counts** (5):
   - `competitors_1mi`, `competitors_3mi`, `competitors_5mi`, `competitors_10mi`, `competitors_20mi`
   - Average: 5.5 competitors within 5 miles

2. **Market Saturation Metrics** (5):
   - `saturation_1mi`, `saturation_3mi`, `saturation_5mi`, `saturation_10mi`, `saturation_20mi`
   - Competitors per 100k population at each radius
   - Average: 6.1 per 100k at 5 miles

3. **Distance-Weighted Competition** (1):
   - `competition_weighted_20mi`
   - Inverse distance weighting (closer competitors = higher impact)

4. **Demographic Interactions** (3):
   - `affluent_market_5mi` = pop_5mi × median_household_income
   - `educated_urban_score` = pct_bachelor_plus × population_density
   - `age_adjusted_catchment_3mi` = median_age × pop_3mi

---

## Current Dataset Structure

### Training Dataset: 741 Dispensaries

**Florida**: 590 training dispensaries
**Pennsylvania**: 151 training dispensaries

### Total Feature Count: 38+ Features

**Phase 1 - Original** (varies by state):
- FL: 22 columns (Placer + regulator data)
- PA: 29 columns (Placer + regulator data)

**Phase 2 - Census Demographics** (24 features):
- 5 census tract identifiers
- 9 home tract demographics (population, age, income, education)
- 5 multi-radius populations (1mi, 3mi, 5mi, 10mi, 20mi)
- 2 derived features (pct_bachelor_plus, population_density)
- 3 data quality flags

**Phase 3a - Competitive Features** (14 features):
- 5 competitor counts at multiple radii
- 5 market saturation metrics
- 1 distance-weighted competition score
- 3 demographic interaction features

### File Locations (All with 78-column schema)

**Primary modeling dataset**:
- `data/processed/combined_with_competitive_features.csv` (937 rows)

**State-specific files** (synchronized):
- `data/processed/FL_combined_dataset_current.csv` (735 rows)
- `data/processed/PA_combined_dataset_current.csv` (202 rows)

**Backups**:
- `data/processed/archive/FL_combined_dataset_20251023_091546_pre_phase3.csv`
- `data/processed/archive/PA_combined_dataset_20251023_091546_pre_phase3.csv`

---

## Data Quality Notes - CRITICAL FOR MODELING

### Complete Training Data: 741/741 (100%)

All 741 training dispensaries (`has_placer_data == True`) have:
- ✅ Complete Placer visit data (target variable)
- ✅ Valid coordinates
- ✅ Complete census features (24 columns)
- ✅ Complete competitive features (14 columns)

### Minor Data Gaps: 3 Dispensaries (0.4%)

**Dispensaries with incomplete demographic interactions**:

1. **Green Dragon** (FL, GEOID 12073000502)
   - Missing: `affluent_market_5mi`
   - Cause: ACS median_household_income suppression

2. **Ethos - Northeast Philadelphia** (PA, GEOID 42101980300)
   - Missing: All 3 demographic interactions
   - Cause: Zero-population institutional tract

3. **Trulieve - South Philadelphia** (PA, GEOID 42101980701)
   - Missing: All 3 demographic interactions
   - Cause: Zero-population institutional tract

**Handling Strategy**:
- Option 1: Median imputation (recommend state-specific medians)
- Option 2: Drop 3 rows (minimal impact: 0.4% of training data)
- Option 3: Model without demographic interactions (not recommended)

**Recommendation**: Use median imputation to preserve all 741 training samples.

### Required Filtering for Model Training

**ALWAYS filter to training dispensaries**:
```python
# Load combined dataset
df = pd.read_csv('data/processed/combined_with_competitive_features.csv')

# Filter to training data only
training_df = df[df['has_placer_data'] == True]  # Returns 741 rows

# Verify
assert len(training_df) == 741
assert training_df['has_placer_data'].all()
```

**DO NOT use regulator-only dispensaries for training** (196 rows with NaN visit data).

---

## Phase 3b Goals & Targets

### Primary Objective

**Build enhanced prediction model with significantly improved performance over PA baseline**

### Performance Targets

- **Primary**: R² > 0.15 (overall, cross-validated)
- **Secondary**: Both FL and PA R² > 0.10 (state-specific)
- **Baseline**: PA model R² = 0.0716 (from 150 dispensaries)
- **Target improvement**: 2x or better (R² ≥ 0.15 = 2.1x improvement)

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Overall R²** | > 0.15 | 5-fold cross-validation |
| **FL R²** | > 0.10 | State-specific validation |
| **PA R²** | > 0.10 | State-specific validation |
| **RMSE** | < 50% of mean visits | Normalized RMSE |
| **MAE** | < 30% of mean visits | Mean absolute error |

### Key Advantages Over PA Model

1. **4.9x larger training set**: 741 vs 150 dispensaries
2. **Multi-state diversity**: Cross-state patterns and universal factors
3. **38+ features**: vs ~15 features in PA model
4. **Multi-radius populations**: 5 buffer zones (1, 3, 5, 10, 20 mi)
5. **Competitive metrics**: Market saturation, distance-weighted competition
6. **Demographic interactions**: Affluent markets, educated urban areas

---

## Recommended Phase 3b Architecture

### Step 1: Data Preparation & Feature Selection

**Module**: `src/modeling/prepare_training_data.py`

**Tasks**:
1. Load and filter to training dispensaries (741 rows)
2. Handle missing demographic interactions (median imputation)
3. Feature correlation analysis and VIF (multicollinearity check)
4. Create state interaction features
5. Train/test split with stratification by state
6. Feature scaling/normalization

**State Interaction Features**:
```python
# Create state-specific versions of key features
'pop_5mi_FL' = pop_5mi × (state == 'FL')
'pop_5mi_PA' = pop_5mi × (state == 'PA')
'competitors_5mi_FL' = competitors_5mi × (state == 'FL')
'competitors_5mi_PA' = competitors_5mi × (state == 'PA')
```

**Output**: Preprocessed training dataset ready for modeling

### Step 2: Model Training - Progressive Approach

**Module**: `src/modeling/train_multi_state_model.py`

**Strategy**: Start simple, add complexity as needed

#### 2.1: Ridge Regression (Baseline)

**Configuration**:
- State interaction terms for key features
- State fixed effect (FL vs PA dummy variable)
- Hyperparameter tuning: alpha ∈ [0.01, 0.1, 1, 10, 100]
- 5-fold cross-validation with state stratification

**Feature selection**:
- Use all census + competitive features
- Add state interaction terms for top 10 features
- Regularization will handle multicollinearity

**Expected performance**: R² = 0.12-0.18 (if successful)

**If R² < 0.15**: Proceed to ensemble methods

#### 2.2: Random Forest (If Ridge insufficient)

**Configuration**:
- n_estimators: 100, 200, 500
- max_depth: 10, 20, None
- min_samples_split: 2, 5, 10
- State as categorical feature

**Advantages**:
- Handles non-linear relationships
- Automatic feature interactions
- Feature importance ranking
- Robust to multicollinearity

**Expected performance**: R² = 0.15-0.22

#### 2.3: XGBoost (If Random Forest promising)

**Configuration**:
- learning_rate: 0.01, 0.05, 0.1
- max_depth: 3, 5, 7
- n_estimators: 100, 200, 500
- State-specific subsample rates

**Advantages**:
- Often best performance
- Handles missing data natively
- Feature importance
- Early stopping

**Expected performance**: R² = 0.16-0.25

#### 2.4: Model Ensemble (If beneficial)

**Strategy**: Stack best performers
- Ridge (interpretability)
- XGBoost (performance)
- Meta-learner: Linear regression

### Step 3: Cross-Validation Strategy

**Module**: `src/modeling/validate_model.py`

**Validation Approaches**:

1. **5-Fold Stratified CV** (primary)
   - Stratify by state (maintain FL/PA ratio in each fold)
   - Report: Overall R², FL R², PA R²

2. **Leave-One-State-Out** (generalization test)
   - Train on FL, test on PA
   - Train on PA, test on FL
   - Assess cross-state generalization

3. **Geographic K-Fold** (spatial autocorrelation)
   - Split by geographic regions within states
   - Prevent spatial leakage

**Metrics to Report**:
- R² (coefficient of determination)
- RMSE (root mean squared error)
- MAE (mean absolute error)
- MAPE (mean absolute percentage error)
- State-specific metrics (FL vs PA)

### Step 4: Model Validation & Analysis

**Residual Analysis**:
- Residual plots (actual vs predicted)
- QQ plots (normality check)
- Residuals by state
- Residuals by competitor density
- Outlier identification

**Feature Importance**:
- Coefficient analysis (Ridge)
- Feature importance scores (RF, XGBoost)
- SHAP values (if time permits)
- Top 10 most predictive features

**State Difference Analysis**:
- Compare FL vs PA performance
- Identify state-specific drivers
- Assess if separate models needed

**Confidence Intervals**:
- Bootstrap confidence intervals
- Prediction intervals for new sites
- Uncertainty quantification

---

## State Differences: Handling Strategy

### Expected Differences Between FL and PA

**Florida**:
- Larger dataset (590 training dispensaries)
- Higher market saturation (more competitors)
- Adult-use + medical market
- Longer market history

**Pennsylvania**:
- Smaller dataset (151 training dispensaries)
- Lower market saturation
- Medical-only market
- Newer market

### Modeling Approach for State Differences

1. **State Interaction Terms** ✅
   - Create FL-specific and PA-specific versions of key features
   - Allows different slopes for population, competition effects

2. **State Fixed Effect** ✅
   - Include state dummy variable
   - Captures baseline visit differences between states

3. **Geographic Cross-Validation** ✅
   - Leave-one-state-out validation
   - Tests generalization across states

4. **State-Specific Metrics** ✅
   - Report R², RMSE separately for FL and PA
   - Identify if one state drives overall performance

5. **Conditional Model Selection** ⚠️
   - If FL R² >> PA R² (gap > 0.10): Consider separate models
   - If FL R² ≈ PA R²: Unified model is appropriate

**Decision Rule**:
```
IF (FL_R2 > 0.15 AND PA_R2 < 0.10):
    Consider training separate FL and PA models
ELSE:
    Use unified model with state interactions
```

---

## Feature Set for Modeling

### Candidate Features (38+ total)

**Target Variable**: `monthly_visits` (or similar from Placer data)

**Core Demographic Features** (recommend all):
- `pop_1mi`, `pop_3mi`, `pop_5mi`, `pop_10mi`, `pop_20mi`
- `median_age`
- `median_household_income`
- `per_capita_income`
- `pct_bachelor_plus`
- `population_density`

**Competitive Features** (recommend all):
- `competitors_1mi`, `competitors_3mi`, `competitors_5mi`, `competitors_10mi`, `competitors_20mi`
- `saturation_1mi`, `saturation_3mi`, `saturation_5mi`, `saturation_10mi`, `saturation_20mi`
- `competition_weighted_20mi`

**Demographic Interactions** (recommend all if imputed):
- `affluent_market_5mi`
- `educated_urban_score`
- `age_adjusted_catchment_3mi`

**State Indicator**:
- `state` (categorical: FL, PA)
- Or: `is_FL` (binary: 1 if FL, 0 if PA)

**Interaction Terms** (create during preprocessing):
- `pop_5mi × state`
- `competitors_5mi × state`
- `saturation_5mi × state`
- `median_household_income × state`

### Features to Exclude

**Identifiers** (not predictive):
- `regulator_name`, `census_geoid`, `census_tract_name`
- `regulator_address`, `regulator_city`, `regulator_zip`

**Data quality flags** (metadata):
- `has_placer_data`, `census_data_complete`, `census_api_error`
- `match_score`, `match_type`, `match_details`

**Redundant/derivative** (choose one from each group):
- Population: Choose 1-2 radii (recommend `pop_5mi` and `pop_20mi`)
- Competitors: Choose 1-2 radii (recommend `competitors_5mi` and `saturation_5mi`)

### Recommended Feature Selection Process

1. **Start with all 38+ features** + state interactions
2. **Calculate VIF** (Variance Inflation Factor)
   - Drop features with VIF > 10 (high multicollinearity)
3. **Train Ridge model** with all remaining features
   - Ridge handles multicollinearity via regularization
4. **Analyze feature importance** from initial model
5. **Refine feature set** based on importance and business logic

---

## Expected Challenges & Solutions

### Challenge 1: Multicollinearity

**Issue**: Multiple radius features highly correlated
- `pop_1mi` ↔ `pop_3mi` ↔ `pop_5mi` (r > 0.8)
- `competitors_1mi` ↔ `competitors_3mi` (r > 0.7)

**Solutions**:
- Ridge/Lasso regularization (handles multicollinearity)
- Feature selection (choose 1-2 radii per metric)
- PCA (if needed, but loses interpretability)

**Recommended**: Use Ridge with all features, monitor VIF.

### Challenge 2: State Imbalance

**Issue**: 590 FL vs 151 PA samples
- Model may overfit to FL patterns
- PA predictions may be less accurate

**Solutions**:
- Stratified sampling in CV (maintain FL/PA ratio)
- State-specific validation metrics
- State interaction terms (different effects per state)
- Optional: State-weighted loss function

**Recommended**: Stratified CV + state interactions.

### Challenge 3: Missing Demographic Interactions

**Issue**: 3 dispensaries missing some features (0.4%)

**Solutions**:
- Option A: Median imputation (state-specific)
- Option B: Drop 3 rows
- Option C: Model without demographic interactions

**Recommended**: State-specific median imputation to preserve all 741 samples.

### Challenge 4: Outliers

**Issue**: Some dispensaries may have extreme visit counts
- High-traffic tourist locations
- Unique competitive positions

**Solutions**:
- Identify outliers via residual analysis
- Optional: Robust regression (Huber loss)
- Optional: Log-transform target variable

**Recommended**: Start with linear target, add log-transform if needed.

---

## Code Structure for Phase 3b

### New Modules to Create

1. **`src/modeling/__init__.py`**
   - Package initialization

2. **`src/modeling/prepare_training_data.py`**
   - Load and filter training data
   - Median imputation for missing values
   - Create state interaction features
   - Train/test split
   - Feature scaling

3. **`src/modeling/train_multi_state_model.py`**
   - Ridge regression with hyperparameter tuning
   - Random Forest (if needed)
   - XGBoost (if needed)
   - Model ensemble (if beneficial)
   - Save best model to `data/models/`

4. **`src/modeling/validate_model.py`**
   - Cross-validation (5-fold stratified)
   - Leave-one-state-out validation
   - Residual analysis
   - Feature importance
   - Performance metrics

5. **`src/modeling/model_utils.py`**
   - Helper functions
   - Metric calculations
   - Plotting utilities

### Expected Outputs

1. **Trained model** - `data/models/multi_state_model_v1.pkl`
2. **Performance report** - `data/models/model_performance_report.json`
3. **Feature importance** - `data/models/feature_importance.csv`
4. **Validation plots** - `data/models/validation_plots/`
5. **Documentation** - `docs/PHASE3B_MODEL_PERFORMANCE.md`

---

## Success Criteria for Phase 3b

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| **Overall R² (CV)** | > 0.15 | 5-fold cross-validation |
| **FL R² (validation)** | > 0.10 | State-specific test set |
| **PA R² (validation)** | > 0.10 | State-specific test set |
| **RMSE** | < 50% of mean visits | Normalized RMSE |
| **Baseline improvement** | > 2x | R² / 0.0716 |
| **Feature importance** | Top 10 identified | From best model |
| **State difference analysis** | Complete | FL vs PA comparison |
| **Model artifact saved** | Yes | .pkl file + metadata |
| **Documentation** | Complete | Performance report |

---

## Quick Start for Phase 3b

```bash
# Navigate to project directory
cd /Users/daniel_insa/Claude/multi-state-dispensary-model

# Verify datasets are ready
python3 -c "
import pandas as pd
df = pd.read_csv('data/processed/combined_with_competitive_features.csv')
training = df[df['has_placer_data'] == True]
print(f'Training dispensaries: {len(training)}')
print(f'Features available: {len(df.columns)}')
print(f'Competitive features: {len([c for c in df.columns if \"competitor\" in c or \"saturation\" in c])}')
"

# Expected output:
# Training dispensaries: 741
# Features available: 78
# Competitive features: 10

# Create modeling directory
mkdir -p src/modeling
mkdir -p data/models
mkdir -p data/models/validation_plots

# Install any missing packages
pip3 install scikit-learn xgboost shap matplotlib seaborn
```

---

## Documentation References

### Phase 3a Documentation (Just Completed)
- **[PHASE3A_COMPETITIVE_FEATURES_COMPLETE.md](PHASE3A_COMPETITIVE_FEATURES_COMPLETE.md)** - Competitive features summary

### Earlier Phase Documentation
- **[PHASE3_CONTINUATION_PROMPT.md](PHASE3_CONTINUATION_PROMPT.md)** - Original Phase 3 plan
- **[PHASE2_COMPLETION_REPORT.md](PHASE2_COMPLETION_REPORT.md)** - Census features (24 columns)
- **[PHASE1_COMPLETION_REPORT.md](PHASE1_COMPLETION_REPORT.md)** - Data integration

### Project Guidelines
- **[CLAUDE.md](../CLAUDE.md)** - Project principles and standards
- **[README.md](../README.md)** - Project overview

---

## Key Questions to Answer in Phase 3b

### Feature Engineering
1. Which radius (1, 3, 5, 10, 20 mi) is most predictive?
2. Is competition or population more important?
3. Do demographic interactions add value?
4. What's the optimal feature subset (avoid multicollinearity)?

### Model Selection
1. Does Ridge regression achieve R² > 0.15 target?
2. Are ensemble methods necessary?
3. How much improvement over PA baseline (0.0716)?
4. What's the optimal regularization strength?

### State Differences
1. Is FL R² significantly different from PA R²?
2. Do FL and PA need separate models?
3. Which features drive each state's performance?
4. Can PA model generalize to FL (and vice versa)?

### Validation
1. How stable is performance across CV folds?
2. Are there systematic errors by geography or competition level?
3. Which dispensaries are outliers (hard to predict)?
4. What's the prediction confidence interval width?

---

## Context for AI Assistant

**You are resuming work on Phase 3b (Model Training & Validation) of the Multi-State Dispensary Prediction Model project.**

**What was just completed**:
- Phase 3a Competitive Features Engineering finished successfully
- 14 competitive features created with 100% completeness (741/741)
- State files synchronized with backups
- All code review issues addressed
- Comprehensive documentation created

**What to do next**:
1. Create data preparation module (imputation, feature selection, train/test split)
2. Build model training pipeline (Ridge → RF → XGBoost if needed)
3. Implement cross-validation with state-aware splits
4. Analyze results and compare FL vs PA performance
5. Target: R² > 0.15 (2x improvement over 0.0716 baseline)

**Critical reminders**:
- ALWAYS filter to training data: `df[df['has_placer_data'] == True]` → 741 rows
- Handle 3 missing demographic interactions (median imputation recommended)
- Create state interaction features for FL vs PA differences
- Use stratified CV to maintain FL/PA ratio
- Report state-specific metrics (FL R² vs PA R²)
- No synthetic data without explicit approval
- Document all methodology decisions

**Modeling strategy**:
1. **Start with Ridge regression** (baseline, interpretable)
2. **Add state interactions** (different effects per state)
3. **Try ensemble methods** only if Ridge R² < 0.15
4. **Progressive complexity** - simplest model that works

**Expected deliverables**:
1. `src/modeling/prepare_training_data.py` - Data preprocessing
2. `src/modeling/train_multi_state_model.py` - Model training
3. `src/modeling/validate_model.py` - Cross-validation & analysis
4. `data/models/multi_state_model_v1.pkl` - Trained model artifact
5. `docs/PHASE3B_MODEL_PERFORMANCE.md` - Results documentation

**Expected timeline**: Phase 3b is a major development effort, likely 4-6 hours of focused work.

---

*Multi-State Dispensary Model - Phase 3b Continuation Prompt*
*Created: October 23, 2025*
*Previous Phase Commit: 1bf91bc*
*Ready to begin: Model Training & Validation*
