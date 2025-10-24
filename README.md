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

**Status**: Phase 3b (Model Training) - Competitive Features Complete, Ready for Model Development

```bash
# Navigate to project directory
cd multi-state-dispensary-model

# Set up environment (first time only)
cp .env.example .env
# Edit .env and add your Census API key

# Install dependencies
pip install -r requirements.txt

# Verify dataset ready for modeling
python3 -c "import pandas as pd; df = pd.read_csv('data/processed/combined_with_competitive_features.csv'); print(f'Training dispensaries: {df[df.has_placer_data==True].shape[0]}')"

# Next: Build Ridge regression model (Phase 3b)
# Coming soon: python3 src/modeling/train_multi_state_model.py
```

## Model Architecture

**Target Performance**: Significantly improved R² over PA model's 0.0716
**Training Data**: ~750 dispensaries across PA & FL
**Features**: Multi-radius population, distance-weighted competition, demographics, state factors
**Model Type**: Enhanced Ridge regression with state interaction terms

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
- ✅ Interactive terminal interface (`TerminalInterface` class)
- ✅ Pretty-print output formatting (PA model style)
- ✅ Batch CSV processing with results export
- **Deliverables**: `src/prediction/predictor.py` (600+ lines), `src/prediction/feature_validator.py` (600+ lines), `src/terminal/cli.py` (545 lines)

### Phase 5a: Model Improvement - Exploration ✅ COMPLETE
- ✅ Data exploration and improvement opportunity analysis
- ✅ Temporal adjustments analysis (PA not needed, FL has 17 sites <12 months)
- ✅ Outlier detection and review (4 sites analyzed, all kept as legitimate)
- ✅ Placer correction methodology designed (7 Insa stores matched)
- ✅ Outlier detection script (`detect_outliers.py` - 353 lines)
- **Deliverables**: Exploration findings, outlier review decisions, correction methodology

### Phase 5b: Data Corrections Implementation ✅ COMPLETE
- ✅ Extracted Insa actual data (10 FL stores, April 2025 monthly transactions)
- ✅ Discovered Placer data is ANNUAL visits (critical finding)
- ✅ Calculated Placer correction factor: 0.5451 (overestimates by 45.5%)
- ✅ Applied Placer correction to all 741 training dispensaries
- ✅ Parsed FL recent openings (59 dispensaries, Oct 2024 - Oct 2025)
- ✅ Matched and adjusted 17 FL sites <12 months operational
- ✅ Created corrected dataset with clear naming convention
- **Scripts**: `extract_insa_data.py` (192 lines), `apply_corrections.py` (488 lines)
- **Deliverables**: `combined_with_competitive_features_corrected.csv` (placer_visits → corrected_visits)
- **Impact**: Mean visits 71,066 → 38,935 (-45.2% correction)
- **Next**: Retrain model v2 with corrected_visits as target

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
- [PHASE5B_CORRECTIONS_COMPLETE.md](docs/PHASE5B_CORRECTIONS_COMPLETE.md) - **Phase 5b complete** - Placer correction + FL temporal adjustments
- [PHASE5_EXPLORATION_COMPLETE.md](docs/PHASE5_EXPLORATION_COMPLETE.md) - **Phase 5a summary** - Data exploration, outlier review
- [MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md](docs/MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md) - **For stakeholders** - Model capabilities, limitations, use cases
- [MODEL_IMPROVEMENT_IDEAS.md](docs/MODEL_IMPROVEMENT_IDEAS.md) - **Roadmap** - Full improvement strategy
- [PHASE4_TERMINAL_INTERFACE_COMPLETE.md](docs/PHASE4_TERMINAL_INTERFACE_COMPLETE.md) - Phase 4 terminal interface completion
- [PHASE3B_MODEL_TRAINING_COMPLETE.md](docs/PHASE3B_MODEL_TRAINING_COMPLETE.md) - Phase 3b model training & validation (✅ R² = 0.1876)
- [CLAUDE.md](CLAUDE.md) - Project guidelines & principles

---

*Building on the foundation of the PA Dispensary Model v3.1 to create the next generation of dispensary site analysis tools.*

**GitHub**: https://github.com/daniel-sarver/multi-state-dispensary-model
**Last Updated**: October 24, 2025 (Phase 5b Complete)