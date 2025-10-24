# Multi-State Dispensary Prediction Model

**Enhanced dispensary visit prediction model for Pennsylvania and Florida**

Building on the proven PA Dispensary Model foundation to create a more powerful multi-state prediction system with improved accuracy through larger training datasets and enhanced feature engineering.

## Project Overview

This project enhances the successful PA Dispensary Model (v3.1) by:
- Training on larger multi-state dataset (~750 dispensaries vs 150-600 single state)
- Integrating FL and PA data with state-specific multipliers
- Enhanced feature engineering for population, competition, and accessibility
- Maintaining proven interface and reporting standards

## Quick Start

**Status**: Phase 6 Complete - Model v2 Production Ready ✅
**CLI Enhancement**: Phase 2 Complete - Coordinate Calculator with Gazetteer Centroids ✅

```bash
# Navigate to project directory
cd multi-state-dispensary-model

# Set up environment (first time only)
cp .env.example .env
# Edit .env and add your Census API key

# Install dependencies
pip install -r requirements.txt

# Verify corrected dataset
python3 -c "import pandas as pd; df = pd.read_csv('data/processed/combined_with_competitive_features_corrected.csv'); print(f'Training dispensaries: {df[df.has_placer_data==True].shape[0]}'); print(f'Target: corrected_visits (ANNUAL)')"

# Train model v2 with corrected data
python3 src/modeling/train_multi_state_model.py

# Run terminal interface (after training)
python3 src/terminal/cli.py

# Test CLI automation data infrastructure (Phase 1 complete)
python3 tests/test_data_loader.py
```

## Model Architecture

**Current Version**: Model v2 (corrected annual visits)
**Target Performance**: R² > 0.15 (significant improvement over baseline 0.0716)
**Training Data**: 741 dispensaries across PA & FL (corrected, calibrated to Insa actual)
**Target Variable**: `corrected_visits` (ANNUAL visits, Placer-corrected with temporal adjustments)
**Features**: 44 features including multi-radius population, distance-weighted competition, demographics, state interactions
**Model Type**: Ridge regression (α=1000) with state interaction terms

## Data Sources

- **Placer Data**: Visit estimates, square footage, coordinates (741 training dispensaries)
- **Census Bureau API**: Demographics by tract via ACS 5-Year (2023)
  - Multi-radius population (1, 3, 5, 10, 20 mile buffers)
  - Age, income, education, population density
- **State Regulator Data**: Complete competitive landscape (937 dispensaries)
- **Insa Performance Data**: Validation benchmark from actual stores
- **Traffic Data**: AADT where available by state (planned)

## Project Structure

```
multi-state-dispensary-model/
├── data/
│   ├── raw/                    # Original datasets (git-ignored)
│   ├── processed/              # FL/PA combined datasets (741 training dispensaries)
│   ├── census/                 # Census tract shapefiles & cache
│   └── models/                 # Trained model artifacts
├── src/
│   ├── data_integration/       # Phase 1: Placer + Regulator merging ✅
│   ├── feature_engineering/    # Phase 2: Census demographics (in progress)
│   ├── modeling/               # Phase 3: Model training (planned)
│   └── reporting/              # Phase 4: Terminal interface (planned)
├── sandbox/                    # Experimentation area
├── tests/                      # Data validation + model tests
├── docs/                       # Methodology, findings, architecture
│   ├── PHASE1_COMPLETION_REPORT.md
│   ├── PHASE2_ARCHITECTURE.md
│   └── archive/                # Historical planning documents
├── .env.example                # Environment variable template
├── .gitignore                  # Protects credentials & data
└── requirements.txt            # Python dependencies
```

## Development Principles

1. **Data Integrity**: Only verified real data sources, no synthetic estimates
2. **Simplicity**: Build on proven PA model patterns and interface design
3. **Organization**: GitHub best practices with comprehensive testing
4. **Learning**: Continuous documentation of key findings and insights

## Model Performance Goals

- **Statistical**: Target R² > 0.15 through enhanced dataset and features
- **Business**: Reliable site ranking and risk assessment for PA/FL expansion
- **Validation**: Cross-state validation and Insa performance benchmarking
- **Confidence**: Proper uncertainty quantification for business decisions

## Project Status

### Phase 1: Data Integration ✅ COMPLETE
- ✅ 741 training-eligible dispensaries (98.8% of target)
- ✅ 937 total dispensaries for competitive landscape
- ✅ Enhanced address matching (96-98 avg confidence)
- ✅ Cannabis-only filtering with brand whitelist
- ✅ Comprehensive test suite

### Phase 2: Census Demographics Integration ✅ COMPLETE
- ✅ 24 census features added (100% coverage)
- ✅ Multi-radius populations (1, 3, 5, 10, 20 miles)
- ✅ Demographics (age, income, education, density)
- ✅ Area-weighted population calculations
- ✅ 99.96% data completeness (7,730 unique tracts)

### Phase 3a: Competitive Features Engineering ✅ COMPLETE
- ✅ 14 competitive features created (100% coverage)
- ✅ Multi-radius competitor counts (1-20 miles)
- ✅ Market saturation metrics (dispensaries per 100k)
- ✅ Distance-weighted competition scores
- ✅ Demographic interaction features (affluent markets, educated urban areas)
- **Deliverables**: `combined_with_competitive_features.csv` (78 columns, 937 rows)

### Phase 3b: Model Training & Validation ✅ COMPLETE
- ✅ Data preparation and feature selection (44 features)
- ✅ Ridge regression with state interactions (alpha=1000)
- ✅ 5-fold cross-validation (R² = 0.1876 ± 0.0645)
- ✅ Leave-one-state-out validation
- ✅ State-specific performance analysis (FL vs PA)
- **Result**: R² = 0.1876 (cross-val), 0.1940 (test) - **2.62x improvement** over baseline
- **Deliverables**: `multi_state_model_v1.pkl`, performance reports, feature importance analysis

### Phase 4: Interface & Reporting ✅ COMPLETE
- ✅ Core prediction module (`MultiStatePredictor` class)
- ✅ State-specific confidence intervals (FL/PA RMSE-based)
- ✅ Bootstrap and normal approximation CI methods
- ✅ Feature contribution analysis
- ✅ Batch prediction capabilities
- ✅ Feature validator class (`FeatureValidator`)
- ✅ Auto-generation of 21 derived features (from 23 base inputs)
- ✅ Range validation with training data statistics
- ✅ Interactive terminal CLI with model info display
- **Deliverables**: `cli.py`, `predictor.py`, `feature_validator.py`

### Phase 5a: Data Quality Exploration ✅ COMPLETE
- ✅ Residual analysis and outlier identification
- ✅ Model performance deep dive (v1 baseline)
- ✅ Validation against Insa actual performance
- ✅ Discovery: Placer data is ANNUAL (not monthly)
- ✅ Discovery: Placer overestimates by ~45%
- **Deliverables**: `PHASE5_DATA_EXPLORATION_FINDINGS.md`, `MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md`

### Phase 5b: Data Corrections ✅ COMPLETE
- ✅ Placer calibration correction (factor: 0.5451, based on 7 Insa stores)
- ✅ FL temporal adjustments (15 sites <12 months, maturity curve applied)
- ✅ Insa actual data extraction (10 FL stores, April 2025)
- ✅ Created corrected dataset with proper naming convention
- ✅ Mean visits corrected: 71,066 → 38,935 (-45.2%)
- **Deliverables**: `combined_with_competitive_features_corrected.csv`, correction scripts, comprehensive documentation
- **Key Discovery**: Model v1 was training on systematically inflated targets

### Phase 6: Model v2 Training ✅ COMPLETE
- ✅ Fixed data leakage (`corrected_visits_step1` excluded from features)
- ✅ Updated training pipeline for corrected dataset
- ✅ Updated CLI for annual visit display
- ✅ Documentation corrections (15 temporal adjustments, not 17)
- ✅ Trained model v2 with `corrected_visits` target (R² = 0.1812)
- ✅ Updated predictor.py to load v2 model by default
- ✅ Verified tests pass with v2 model
- ✅ Compared v1 vs v2 performance (45% more accurate in absolute terms)
- ✅ Created comprehensive Phase 6 documentation
- **Result**: Model v2 predictions within 20% of Insa actual (vs v1's 45% overestimate)
- **Deliverables**: `multi_state_model_v2.pkl`, `PHASE6_MODEL_V2_COMPLETE.md`, `MODEL_V1_VS_V2_COMPARISON.txt`

### CLI Automation: Phase 1 Data Infrastructure ✅ COMPLETE
- ✅ Custom exception classes for explicit error handling (no fallbacks)
- ✅ Multi-state data loader with **full statewide census coverage**
- ✅ 7,624 census tracts loaded (4,983 FL + 2,641 PA) - **12.7x improvement**
- ✅ 741 dispensaries for competition analysis
- ✅ Comprehensive test suite (8 tests, all passing)
- ✅ Codex review fix: Increased coverage from 600 → 7,624 tracts
- **Result**: 100% FL/PA geographic coverage for coordinate-based feature calculation
- **Deliverables**: `data_loader.py`, `exceptions.py`, `test_data_loader.py`, implementation documentation

### CLI Automation: Phase 2 Coordinate Calculator ✅ COMPLETE (with Codex Fix)
- ✅ Coordinate-based feature calculator class (577 lines)
- ✅ Population calculation at 1, 3, 5, 10, 20 mile radii
- ✅ Competition count and normalized metrics (10 features)
- ✅ Distance-weighted competition score
- ✅ Census tract matching via API + demographics extraction (7 features)
- ✅ Master method: 3-4 inputs → 23 base features automatically (87% input reduction)
- ✅ Enhanced data loader with real per-tract centroids from Census Gazetteer
- ✅ **Codex Fix Applied**: Replaced county approximations with authoritative Gazetteer centroids
- **Result**: Users input only (state, lat, lon, sq_ft) - accurate population at ALL radii
- **Deliverables**: `coordinate_calculator.py`, enhanced `data_loader.py`, `download_gazetteer_files.sh`, documentation
- **Next**: Phase 3 - CLI Integration (connect calculator to terminal interface)


## Key Achievements

**Phase 1 Results**:
- 15.2% increase in training data through enhanced matching (+98 dispensaries)
- 4.9x larger training set than original PA model (741 vs ~150)
- Complete competitive landscape coverage (937 sites)
- Production-ready data integration pipeline

**Phase 2 Production Results**:
- 741/741 training dispensaries with complete census demographics (100%)
- 7,730 unique census tracts processed across FL and PA
- 99.96% data completeness (3 tracts with standard ACS suppressions)
- Multi-radius populations (1, 3, 5, 10, 20 miles) with area-weighted aggregation
- 24+ new census columns: demographics, population density, education, income
- Mathematically correct area-weighting prevents rural over-counting
- State-specific Albers projections (EPSG:3086 FL, EPSG:6565 PA)

**Phase 3 Production Results**:
- ✅ **R² = 0.1876 (cross-validated)** - Target achieved (> 0.15)
- ✅ **2.62x improvement** over baseline PA model (0.0716 → 0.1876)
- ✅ **Test set R² = 0.1940** - Robust out-of-sample performance
- 44 engineered features with state interactions (FL vs PA)
- Ridge regression (alpha=1000) handles multicollinearity effectively
- Square footage dominates predictions (+2,945 coefficient)
- Competition significantly reduces visits (all negative coefficients)
- Production-ready model artifact (4.20 KB) with scaler and metadata

**Phase 4 Progress** (In Progress):
- ✅ **Core prediction module built** - `MultiStatePredictor` class (600+ lines)
- ✅ **State-specific confidence intervals** - FL RMSE (33,162), PA RMSE (56,581)
- ✅ **Bootstrap CI implementation** - 1000 iterations for accurate uncertainty
- ✅ **Dynamic metric loading** - Reads from training_report (no hardcoded values)
- ✅ **Feature contribution analysis** - Shows top drivers for each prediction
- ✅ **Batch prediction mode** - Process multiple sites efficiently
- ✅ **Feature validator built** - `FeatureValidator` class (600+ lines)
- ✅ **Auto-feature generation** - 21 derived features from 23 base inputs (48% reduction)
- ✅ **Range validation** - Training data statistics with warnings/errors
- ✅ **Formula accuracy** - 100% match with training pipeline (0% error)
- ✅ **Terminal interface built** - `TerminalInterface` class (545 lines)
- ✅ **Interactive single-site analysis** - User-friendly feature collection
- ✅ **Batch CSV processing** - Multiple sites with results export
- ✅ **Professional output formatting** - PA model style with visual hierarchy
- Production-ready end-to-end prediction system with comprehensive error handling

## Documentation

See [docs/README.md](docs/README.md) for complete documentation index.

**Key Documents**:
- [PHASE6_MODEL_V2_COMPLETE.md](docs/PHASE6_MODEL_V2_COMPLETE.md) - **Phase 6 complete** - Model v2 with corrected data (R² = 0.1812, 45% more accurate)
- [MODEL_V1_VS_V2_COMPARISON.txt](docs/MODEL_V1_VS_V2_COMPARISON.txt) - **v1 vs v2** - Performance comparison and recommendations
- [PHASE5B_CORRECTIONS_COMPLETE.md](docs/PHASE5B_CORRECTIONS_COMPLETE.md) - **Phase 5b** - Placer correction + FL temporal adjustments
- [PHASE5_EXPLORATION_COMPLETE.md](docs/PHASE5_EXPLORATION_COMPLETE.md) - **Phase 5a** - Data exploration, outlier review
- [MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md](docs/MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md) - **For stakeholders** - Model capabilities, limitations, use cases
- [MODEL_IMPROVEMENT_IDEAS.md](docs/MODEL_IMPROVEMENT_IDEAS.md) - **Roadmap** - Full improvement strategy
- [PHASE4_TERMINAL_INTERFACE_COMPLETE.md](docs/PHASE4_TERMINAL_INTERFACE_COMPLETE.md) - Phase 4 terminal interface completion
- [PHASE3B_MODEL_TRAINING_COMPLETE.md](docs/PHASE3B_MODEL_TRAINING_COMPLETE.md) - Phase 3b model training & validation
- [CLAUDE.md](CLAUDE.md) - Project guidelines & principles

---

*Building on the foundation of the PA Dispensary Model v3.1 to create the next generation of dispensary site analysis tools.*

**GitHub**: https://github.com/daniel-sarver/multi-state-dispensary-model
**Last Updated**: October 24, 2025 (Phase 6 Complete - Model v2 Production Ready)