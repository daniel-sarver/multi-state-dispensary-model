# Phase 4 Continuation: Terminal Interface Development

**Date**: October 23, 2025
**Phase**: Phase 4 - Terminal Interface & Production Deployment
**Status**: Core Modules Complete ✅, Terminal Interface Next 🚧
**Last Commit**: 76ed484 - "Phase 4: Implement feature validator with formula corrections"

---

## 📋 What's Been Completed

### ✅ Core Prediction Module (`src/prediction/predictor.py`)

**File**: 600+ lines of production-ready prediction code
**Location**: `/Users/daniel_insa/Claude/multi-state-dispensary-model/src/prediction/predictor.py`

#### `MultiStatePredictor` Class - Full API

**Key Methods**:
1. **`predict(features_dict)`** - Point prediction from 44 features
2. **`predict_with_confidence(features_dict, confidence=0.95, method='normal')`**
   - State-specific RMSE: FL (33,162), PA (56,581)
   - Methods: 'normal' (fast) or 'bootstrap' (1000 iterations)
3. **`get_feature_contributions(features_dict)`** - Feature impact analysis
4. **`get_top_drivers(features_dict, n=5)`** - Top N influential features
5. **`predict_batch(features_df, include_confidence=False)`** - Batch processing
6. **`get_model_info()`** - Model metadata (R², RMSE, state performance)

**Documentation**: [PHASE4_PREDICTION_MODULE_COMPLETE.md](PHASE4_PREDICTION_MODULE_COMPLETE.md)

### ✅ Feature Validator Module (`src/prediction/feature_validator.py`)

**File**: 600+ lines of validation and auto-generation code
**Location**: `/Users/daniel_insa/Claude/multi-state-dispensary-model/src/prediction/feature_validator.py`

#### `FeatureValidator` Class - Full API

**Key Methods**:
1. **`prepare_features(base_features, state)`** - Main entry point
   - Input: 23 base features + state ('FL' or 'PA')
   - Output: Complete dict with all 44 features
   - Auto-generates 21 derived features (48% input reduction)
2. **`validate_batch(features_df, state_column)`** - Batch validation
3. **`get_feature_ranges()`** - Training data min/max/mean/median
4. **`get_feature_info(feature_name)`** - Feature metadata
5. **`get_required_base_features()`** - List of 23 required inputs
6. **`get_auto_generated_features()`** - List of 21 auto-generated

**Features**:
- ✅ Range validation using training statistics
- ✅ Auto-generation of state interactions (10 features)
- ✅ Auto-generation of state indicators (is_FL, is_PA)
- ✅ Auto-generation of derived features (saturation, demographics)
- ✅ Formula accuracy: 100% match with training pipeline
- ✅ Comprehensive error messages and warnings

**Codex Review**: All 4 formula errors fixed (Oct 23, 2025)
- affluent_market_5mi: 10,000× scaling error corrected
- educated_urban_score: 1,000× scaling error corrected
- age_adjusted_catchment_3mi: Wrong formula fixed
- competition_weighted_20mi: Now required as input (distance matrix)

**Documentation**: [PHASE4_FEATURE_VALIDATOR_COMPLETE.md](PHASE4_FEATURE_VALIDATOR_COMPLETE.md)

---

## 🎯 Next Steps: Terminal Interface Development

### Priority 1: Interactive CLI (`src/terminal/cli.py`)

**Goal**: User-friendly terminal interface for interactive predictions

**Required Functionality**:

1. **Interactive Input Collection**
   ```
   ============================================================
   MULTI-STATE DISPENSARY PREDICTION - SITE ANALYSIS
   ============================================================

   State Selection:
     [1] Florida
     [2] Pennsylvania
   > Select state (1-2): 1

   Dispensary Characteristics:
   > Square footage: 4587

   Multi-Radius Populations:
   > Population (1 mile): 5950
   > Population (3 miles): 52821
   > Population (5 miles): 71106
   > Population (10 miles): 176028
   > Population (20 miles): 563096

   Competition Analysis:
   > Competitors (1 mile): 0
   > Competitors (3 miles): 2
   > Competitors (5 miles): 3
   > Competitors (10 miles): 5
   > Competitors (20 miles): 13
   > Distance-weighted competition (20mi): 1.78

   Census Demographics:
   > Total population: 4062
   > Median age: 29.1
   > Median household income: 76458
   > Per capita income: 37439
   > Total pop 25+: 2369
   > Bachelor's degrees: 424
   > Master's degrees: 125
   > Professional degrees: 0
   > Doctorate degrees: 18
   > Population density (per sq mi): 890.55
   > Tract area (sq meters): 4561619.35

   Validating inputs...
   ✅ All inputs valid

   Generating prediction...
   ```

2. **Real-time Validation**
   - Use `FeatureValidator` to check inputs as entered
   - Show warnings for out-of-range values
   - Allow retry on invalid input
   - Provide helpful error messages

3. **Pretty-Print Output** (match PA model style)
   ```
   ============================================================
   PREDICTION RESULTS
   ============================================================

   Site Summary:
     State:                 Florida
     Square Footage:        4,587 sq ft
     Population (5mi):      71,106
     Competitors (5mi):     3
     Market Saturation:     4.22 per 100k

   Prediction:
     Expected Monthly Visits:        79,893
     95% Confidence Interval:        14,897 - 144,889
     Confidence Level:               MODERATE

   Uncertainty:
     Method:                         Normal Approximation
     State RMSE:                     33,162 (Florida-specific)
     Prediction Range:               ±64,996 visits

   Top Feature Drivers:
     ✅ Square Footage              +10,325 visits (strong positive)
     ⚠️  Saturation (5mi, FL)       +2,898 visits
     ⚠️  Competition (5mi, FL)      +1,305 visits
     ⚠️  Median Income (FL)         +1,251 visits
     ⚠️  Competitors (1mi)          +1,250 visits

   Model Performance:
     Test R²:                        0.194
     Cross-Validation R²:            0.187 ± 0.065
     Improvement over Baseline:      2.62x

   Interpretation:
     This site shows MODERATE predicted performance with HIGH
     uncertainty. The wide confidence interval (130k range) reflects
     the model's limited explanatory power (R² = 0.19). Consider this
     prediction as directional guidance rather than a precise forecast.

     Key factors: Large square footage is the strongest positive driver.
     Competition and market saturation have mixed effects.

   ============================================================

   Options:
     [1] Analyze another site
     [2] Export to CSV
     [3] Exit
   >
   ```

4. **Batch Mode** (optional but recommended)
   - Accept CSV file path
   - Process all rows using `validator.validate_batch()`
   - Generate predictions using `predictor.predict_batch()`
   - Export results to CSV with predictions and confidence intervals

5. **Input Helpers** (optional but nice-to-have)
   - Show example values from training data
   - Provide typical ranges for each feature
   - Offer to load from CSV template
   - Save inputs to CSV for future use

**Recommended Structure**:
```python
# src/terminal/cli.py

import sys
from typing import Dict, Any
from src.prediction.predictor import MultiStatePredictor
from src.prediction.feature_validator import FeatureValidator


class TerminalInterface:
    """Interactive CLI for multi-state dispensary predictions."""

    def __init__(self):
        self.predictor = MultiStatePredictor()
        self.validator = FeatureValidator()

    def run(self):
        """Main entry point - run interactive session."""
        self.print_header()

        while True:
            mode = self.select_mode()

            if mode == 'single':
                self.run_single_site_analysis()
            elif mode == 'batch':
                self.run_batch_analysis()
            elif mode == 'exit':
                break

    def select_mode(self) -> str:
        """Let user choose single vs batch mode."""
        # Implementation

    def run_single_site_analysis(self):
        """Interactive single-site prediction."""
        state = self.prompt_state()
        base_features = self.prompt_base_features(state)

        # Validate and generate features
        try:
            complete_features = self.validator.prepare_features(
                base_features, state
            )
        except ValueError as e:
            print(f"\n❌ Validation Error: {e}")
            return

        # Generate prediction
        result = self.predictor.predict_with_confidence(
            complete_features, method='normal'
        )

        # Get top drivers
        top_drivers = self.predictor.get_top_drivers(
            complete_features, n=5
        )

        # Pretty-print results
        self.print_results(
            state, base_features, result, top_drivers
        )

    def run_batch_analysis(self):
        """Batch prediction from CSV file."""
        # Implementation

    def prompt_state(self) -> str:
        """Prompt user to select FL or PA."""
        # Implementation

    def prompt_base_features(self, state: str) -> Dict[str, Any]:
        """Prompt for all 23 base features."""
        # Implementation

    def print_results(self, state, features, result, drivers):
        """Pretty-print prediction results."""
        # Implementation

    def print_header(self):
        """Print CLI header."""
        print("=" * 60)
        print("MULTI-STATE DISPENSARY PREDICTION MODEL")
        print("Powered by Ridge Regression (R² = 0.194)")
        print("=" * 60)


if __name__ == "__main__":
    cli = TerminalInterface()
    cli.run()
```

### Priority 2: Insa Validation Module (`src/validation/insa_validator.py`)

**Goal**: Validate model predictions against Insa's actual store performance

**Required Functionality**:

1. **Load Insa Actual Performance Data**
   - Which stores do we have data for? (FL, MA, CT?)
   - What format is the data in?
   - What time period does it cover?
   - **Action Needed**: Clarify data availability with Daniel

2. **Feature Collection for Insa Sites**
   - Collect all 44 features for each Insa store
   - May require manual data gathering or API calls
   - Ensure feature definitions match training data

3. **Generate Predictions for Insa Sites**
   ```python
   # For each Insa store
   features = collect_features(insa_store)
   prediction = predictor.predict_with_confidence(features)
   actual = insa_store.actual_visits
   ```

4. **Error Analysis**
   ```python
   # Calculate metrics
   rmse = np.sqrt(mean((actual - predicted)^2))
   mae = mean(abs(actual - predicted))
   mape = mean(abs((actual - predicted) / actual)) * 100

   # By state
   fl_rmse, pa_rmse = calculate_by_state(results)

   # By store characteristics
   by_size = group_by_square_footage(results)
   by_competition = group_by_competitors(results)
   ```

5. **Confidence Interval Calibration**
   ```python
   # Check CI coverage
   within_ci = sum(
       (actual >= ci_lower) & (actual <= ci_upper)
   ) / n_stores

   # Should be ~95% for 95% CI
   # If significantly different, may need to adjust intervals
   ```

6. **Visualization and Reporting**
   - Predicted vs Actual scatter plot
   - Residuals plot
   - Error distribution by state
   - Summary statistics table

**Recommended Structure**:
```python
# src/validation/insa_validator.py

import pandas as pd
import numpy as np
from src.prediction.predictor import MultiStatePredictor
from src.prediction.feature_validator import FeatureValidator


class InsaValidator:
    """Validate model predictions against Insa actual performance."""

    def __init__(self,
                 insa_data_path: str,
                 predictor: MultiStatePredictor = None):
        self.insa_data = pd.read_csv(insa_data_path)
        self.predictor = predictor or MultiStatePredictor()
        self.validator = FeatureValidator()

    def validate_predictions(self) -> pd.DataFrame:
        """Generate predictions for all Insa stores and compare to actuals."""
        results = []

        for idx, store in self.insa_data.iterrows():
            # Collect features
            features = self.collect_store_features(store)

            # Generate prediction
            result = self.predictor.predict_with_confidence(features)

            # Compare to actual
            actual = store['actual_monthly_visits']
            error = result['prediction'] - actual
            pct_error = (error / actual) * 100
            within_ci = (
                actual >= result['ci_lower'] and
                actual <= result['ci_upper']
            )

            results.append({
                'store_name': store['name'],
                'state': store['state'],
                'actual': actual,
                'predicted': result['prediction'],
                'ci_lower': result['ci_lower'],
                'ci_upper': result['ci_upper'],
                'error': error,
                'pct_error': pct_error,
                'within_ci': within_ci
            })

        return pd.DataFrame(results)

    def collect_store_features(self, store) -> Dict[str, float]:
        """Collect 44 features for an Insa store."""
        # Implementation depends on data availability
        # May require API calls, manual entry, or database queries
        pass

    def calculate_metrics(self, results_df: pd.DataFrame) -> Dict:
        """Calculate validation metrics."""
        return {
            'rmse': np.sqrt(np.mean(results_df['error']**2)),
            'mae': np.mean(np.abs(results_df['error'])),
            'mape': np.mean(np.abs(results_df['pct_error'])),
            'ci_coverage': results_df['within_ci'].mean(),
            'n_stores': len(results_df)
        }

    def generate_report(self, output_path: str = None):
        """Generate validation report with visualizations."""
        results = self.validate_predictions()
        metrics = self.calculate_metrics(results)

        # Print summary
        print("=" * 60)
        print("INSA VALIDATION REPORT")
        print("=" * 60)
        print(f"Stores Validated: {metrics['n_stores']}")
        print(f"RMSE: {metrics['rmse']:,.0f} visits/month")
        print(f"MAE: {metrics['mae']:,.0f} visits/month")
        print(f"MAPE: {metrics['mape']:.1f}%")
        print(f"CI Coverage: {metrics['ci_coverage']:.1%} (target: 95%)")

        # Save results if path provided
        if output_path:
            results.to_csv(output_path, index=False)
            print(f"\n✅ Results saved to {output_path}")
```

---

## 🔑 Key Technical Details

### Model Artifact Structure

```python
# data/models/multi_state_model_v1.pkl
{
    'model': Pipeline([('scaler', StandardScaler()), ('ridge', Ridge(alpha=1000))]),
    'scaler': StandardScaler(),  # Fitted on training data
    'feature_names': [...44 features...],
    'best_alpha': 1000,
    'training_date': '2025-10-23T10:33:44.983087',
    'training_report': {
        'test_set': {'r2': 0.1940, 'rmse': 39023.87, ...},
        'state_performance': {
            'florida': {'r2': 0.0493, 'rmse': 33161.89, ...},
            'pennsylvania': {'r2': -0.0271, 'rmse': 56580.60, ...}
        },
        'cross_validation': {'r2_mean': 0.1872, ...}
    }
}
```

### 44 Required Features

**User Must Provide (23 features)**:
1. `sq_ft`
2-6. `pop_1mi`, `pop_3mi`, `pop_5mi`, `pop_10mi`, `pop_20mi`
7-11. `competitors_1mi`, `competitors_3mi`, `competitors_5mi`, `competitors_10mi`, `competitors_20mi`
12. `competition_weighted_20mi` (pre-computed from distance matrix)
13-23. Demographics: `total_population`, `median_age`, `median_household_income`, `per_capita_income`, `total_pop_25_plus`, `bachelors_degree`, `masters_degree`, `professional_degree`, `doctorate_degree`, `population_density`, `tract_area_sqm`

**System Auto-Generates (21 features)**:
24-25. State indicators: `is_FL`, `is_PA`
26-30. Saturation: `saturation_1mi`, `saturation_3mi`, `saturation_5mi`, `saturation_10mi`, `saturation_20mi`
31-34. Demographics: `pct_bachelor_plus`, `affluent_market_5mi`, `educated_urban_score`, `age_adjusted_catchment_3mi`
35-44. State interactions: `pop_5mi_FL`, `pop_5mi_PA`, `pop_20mi_FL`, `pop_20mi_PA`, `competitors_5mi_FL`, `competitors_5mi_PA`, `saturation_5mi_FL`, `saturation_5mi_PA`, `median_household_income_FL`, `median_household_income_PA`

---

## 📊 Model Performance Summary

**Overall**:
- Test R² = 0.1940
- Test RMSE = 39,024 visits
- CV R² = 0.1872 ± 0.0645
- 2.62x improvement over baseline

**Florida**:
- Test R² = 0.0493
- Test RMSE = 33,162 visits (lower uncertainty)
- n = 119 test samples

**Pennsylvania**:
- Test R² = -0.0271
- Test RMSE = 56,581 visits (higher uncertainty)
- n = 30 test samples (small sample)

**Key Drivers**:
- Square footage: +2,945 visits/1,000 sq ft (strongest predictor)
- Competition: Negative impact (all competition features negative)
- State effects: PA baseline higher than FL
- Population density: Negative coefficient (suburban sweet spot)

---

## 🚀 Quick Start After Compacting

```bash
# 1. Navigate to project
cd /Users/daniel_insa/Claude/multi-state-dispensary-model

# 2. Test prediction module
python3 src/prediction/predictor.py
# Should show: Model loaded, example prediction, top drivers, CIs

# 3. Test feature validator
python3 src/prediction/feature_validator.py
# Should show: Validation test, auto-generated features, integration test

# 4. Start building Terminal Interface
# Create src/terminal/cli.py
# Implement TerminalInterface class
# Test with: python3 src/terminal/cli.py
```

---

## 📁 Project Structure

```
multi-state-dispensary-model/
├── data/
│   ├── models/
│   │   ├── multi_state_model_v1.pkl          # Model artifact (5.42 KB)
│   │   └── feature_ranges.json               # Training statistics (git-ignored)
│   └── processed/
│       └── combined_with_competitive_features.csv  # Training data (937 rows, 78 cols)
├── src/
│   ├── prediction/
│   │   ├── __init__.py
│   │   ├── predictor.py                      # ✅ Complete (600+ lines)
│   │   └── feature_validator.py              # ✅ Complete (600+ lines)
│   ├── terminal/
│   │   └── cli.py                            # 🚧 Next priority
│   └── validation/
│       └── insa_validator.py                 # 🚧 To build
├── docs/
│   ├── PHASE4_PREDICTION_MODULE_COMPLETE.md
│   ├── PHASE4_FEATURE_VALIDATOR_COMPLETE.md
│   └── PHASE4_TERMINAL_INTERFACE_CONTINUATION.md  # This file
└── README.md
```

---

## ⚠️ Important Notes

### Model Limitations

1. **R² = 0.19 means**:
   - Model explains ~19% of visit variance
   - 81% remains unexplained (product, marketing, staff, etc.)
   - Use for directional guidance, not precise forecasts
   - Always provide confidence intervals

2. **Wide Confidence Intervals**:
   - Typical 95% CI spans ±60,000 - 110,000 visits
   - Reflects genuine model uncertainty
   - Critical for honest business communication

3. **State-Specific Performance**:
   - Florida: Weaker predictions (R² = 0.0493)
   - Pennsylvania: Very weak (R² = -0.0271, n=30)
   - Overall performance drives utility

### Data Requirements for New Sites

For terminal interface, users need to gather:
1. **Easy**: State, square footage, address/coordinates
2. **Requires geocoding**: Multi-radius populations (1-20 miles)
3. **Requires competitor analysis**: Counts at multiple radii
4. **Requires census data**: Demographics by tract
5. **Requires calculation**: Saturation, interactions, weighted competition

**Future Enhancement**: Build helper functions to auto-calculate from minimal inputs (address + square footage).

---

## 🎯 Success Metrics for Terminal Interface

**Functional**:
- ✅ User can interactively enter 23 base features
- ✅ System auto-generates remaining 21 features
- ✅ Predictions generated with confidence intervals
- ✅ Top feature drivers displayed
- ✅ Graceful error handling with helpful messages
- ✅ Batch mode for CSV inputs

**Performance**:
- Prediction latency < 1 second
- Bootstrap CI < 5 seconds
- Batch mode processes 10+ sites/minute

**User Experience**:
- Clear, professional output formatting
- Matches PA model interface style
- Helpful prompts with examples
- Real-time validation feedback

---

## 🔜 After Terminal Interface

1. **Helper Functions** (Medium Priority)
   - Geocoding: address → coordinates
   - Census wrapper: coordinates → demographics
   - Competition calculator: coordinates → weighted competition
   - Complete site evaluation from minimal inputs

2. **Documentation** (Low Priority)
   - User guide for CLI
   - API documentation
   - Tutorial videos/screenshots
   - Troubleshooting guide

3. **Testing & Quality** (High Priority)
   - Unit tests for CLI functions
   - Integration tests for full workflow
   - User acceptance testing with Insa team
   - Performance benchmarking

---

## ✅ Pre-Compacting Checklist

- ✅ Core prediction module complete and tested
- ✅ Feature validator complete with Codex fixes applied
- ✅ All formulas validated against training data (100% accuracy)
- ✅ Documentation updated (README, docs/README, completion reports)
- ✅ Changes committed and pushed (commit 76ed484)
- ✅ Continuation prompt created

**Status**: ✅ **READY TO COMPACT - Terminal Interface Development Next**

---

## 📚 Documentation References

**Phase 4 Progress**:
- [PHASE4_PREDICTION_MODULE_COMPLETE.md](PHASE4_PREDICTION_MODULE_COMPLETE.md)
- [PHASE4_FEATURE_VALIDATOR_COMPLETE.md](PHASE4_FEATURE_VALIDATOR_COMPLETE.md)
- [README.md](../README.md) - Project overview and status
- [docs/README.md](README.md) - Documentation index

**Model Details**:
- [PHASE3B_MODEL_TRAINING_COMPLETE.md](PHASE3B_MODEL_TRAINING_COMPLETE.md)
- [CODEX_REVIEW_DOUBLE_SCALING_FIX.md](CODEX_REVIEW_DOUBLE_SCALING_FIX.md)

**Project Guidelines**:
- [CLAUDE.md](../CLAUDE.md) - Data integrity and development standards

---

*Multi-State Dispensary Model - Phase 4 Terminal Interface Continuation*
*Date: October 23, 2025*
*Commit: 76ed484*
*Next: Terminal Interface Development (src/terminal/cli.py)*
