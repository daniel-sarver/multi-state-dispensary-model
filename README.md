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

**Status**: In Development - Phase 1 (Data Integration)

```bash
# Navigate to project directory
cd multi-state-dispensary-model

# Run analysis (when ready)
python3 run_multi_state_analysis.py
```

## Model Architecture

**Target Performance**: Significantly improved R² over PA model's 0.0716
**Training Data**: ~750 dispensaries across PA & FL
**Features**: Multi-radius population, distance-weighted competition, demographics, state factors
**Model Type**: Enhanced Ridge regression with state interaction terms

## Data Sources

- **Placer Data**: Visit estimates, square footage, coordinates (~750 dispensaries)
- **Census Data**: Demographics by tract (both states)
- **State Regulator Data**: Complete competitive landscape
- **Insa Performance Data**: Validation benchmark from actual stores
- **Traffic Data**: AADT where available by state

## Project Structure

```
multi-state-dispensary-model/
├── data/
│   ├── raw/                    # Original datasets
│   ├── processed/              # Cleaned, integrated data
│   └── models/                 # Trained model artifacts
├── src/
│   ├── data_integration/       # Placer + Census + Regulator merging
│   ├── feature_engineering/    # Population, competition, traffic analysis
│   ├── modeling/               # Training, validation, prediction
│   └── reporting/              # Terminal interface + outputs
├── sandbox/                    # Experimentation area
├── tests/                      # Data validation + model tests
└── docs/                       # Methodology, findings, learnings
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

## Status

- ✅ Project structure created
- 🔄 Phase 1: Data Integration (in progress)
- ⏳ Phase 2: Enhanced Feature Engineering
- ⏳ Phase 3: Model Development
- ⏳ Phase 4: Interface & Reporting

---

*Building on the foundation of the PA Dispensary Model v3.1 to create the next generation of dispensary site analysis tools.*