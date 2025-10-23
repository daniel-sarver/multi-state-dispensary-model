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

### Phase 3b: Model Training & Validation 🚧 NEXT
- ⏳ Data preparation and feature selection
- ⏳ Ridge regression with state interactions
- ⏳ Ensemble methods (RF, XGBoost) if needed
- ⏳ Geographic cross-validation
- ⏳ State-specific performance analysis (FL vs PA)
- **Target**: R² > 0.15 (2x improvement over PA baseline)

### Phase 4: Interface & Reporting ⏳ PLANNED
- Terminal interface adaptation for multi-state predictions
- Enhanced reporting system
- Production deployment

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

## Documentation

See [docs/README.md](docs/README.md) for complete documentation index.

**Key Documents**:
- [PHASE1_COMPLETION_REPORT.md](docs/PHASE1_COMPLETION_REPORT.md) - Phase 1 summary & results
- [PHASE2_COMPLETION_REPORT.md](docs/PHASE2_COMPLETION_REPORT.md) - Phase 2 production run summary & results
- [PHASE2_ARCHITECTURE.md](docs/PHASE2_ARCHITECTURE.md) - Census integration architecture (v1.2)
- [PHASE2_DATA_QUALITY_NOTES.md](docs/PHASE2_DATA_QUALITY_NOTES.md) - Data quality analysis, ACS suppressions, downstream compatibility
- [CODEX_REVIEW_PHASE2.md](docs/CODEX_REVIEW_PHASE2.md) - Critical architecture fixes
- [CLAUDE.md](CLAUDE.md) - Project guidelines & principles

---

*Building on the foundation of the PA Dispensary Model v3.1 to create the next generation of dispensary site analysis tools.*

**GitHub**: https://github.com/daniel-sarver/multi-state-dispensary-model
**Last Updated**: October 23, 2025