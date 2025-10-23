# Phase 4 Continuation Prompt: Terminal Interface & Production Deployment

**Date Created**: October 23, 2025
**Phase**: Phase 4 - Terminal Interface & Production Deployment
**Previous Phase**: Phase 3b - Model Training & Validation (✅ COMPLETE)
**Project**: Multi-State Dispensary Prediction Model (PA & FL)

---

## 📋 Context: Where We Are

### Phase 3b Status: ✅ COMPLETE

**Model Performance**:
- Ridge Regression with Pipeline (alpha=1000)
- Cross-Validation R² = **0.1872 ± 0.0645** ✅ (Target: > 0.15)
- Test Set R² = **0.1940** ✅ (Robust out-of-sample)
- 2.61x improvement over baseline PA model (0.0716 → 0.1872)
- 44 engineered features with FL/PA state interactions
- Production-ready model artifact: `data/models/multi_state_model_v1.pkl` (5.42 KB)

**State-Specific Performance**:
- Florida R² = 0.0493 (n=119 test samples)
- Pennsylvania R² = -0.0271 (n=30 test samples)
- R² Difference = 0.0765 < 0.10 threshold (unified model appropriate)

**Critical Bug Fixed** (Oct 23, 2025):
- ⚠️ Double-scaling bug resolved (test data was scaled twice by Pipeline)
- Test R² corrected from -0.1788 → 0.1940
- See `docs/CODEX_REVIEW_DOUBLE_SCALING_FIX.md` for full details
- All metrics now validated and production-ready

**Training Data**:
- 741 total training dispensaries (FL: 590, PA: 151)
- 592 training samples (80%), 149 test samples (20%)
- 937 total dispensaries for competitive landscape
- 44 features: demographics, competition, populations, state interactions

---

## 🎯 Phase 4 Objectives

### Primary Goal
Build terminal interface for multi-state dispensary visit predictions, adapting the proven PA Dispensary Model CLI to work with the enhanced multi-state model.

### Success Criteria

**Functional Requirements**:
1. ✅ Command-line interface accepting 44 feature inputs
2. ✅ State selection (FL or PA) with proper state interaction handling
3. ✅ Load model artifact and generate predictions
4. ✅ Input validation (ranges, data types, required fields)
5. ✅ Confidence intervals around predictions
6. ✅ Feature sensitivity analysis (impact of changing key features)
7. ✅ Batch prediction mode (compare multiple sites)

**Performance Requirements**:
- Prediction latency < 1 second per site
- Graceful error handling for invalid inputs
- Clear, actionable output for business users

**Validation Requirements**:
- Test against Insa actual store performance (FL, MA, CT)
- Calculate prediction error metrics (RMSE, MAE, MAPE)
- Identify systematic biases
- Calibrate confidence intervals based on real performance

**Documentation Requirements**:
- User manual for terminal interface
- Model interpretation guide (business-friendly)
- Limitations documentation
- Installation and deployment guide

---

## 📊 Model Artifact Details

### Files Available

**Model Artifacts** (in `data/models/`):
- `multi_state_model_v1.pkl` (5.42 KB) - Trained Pipeline with StandardScaler + Ridge
- `model_performance_report.json` - Training metrics and state performance
- `feature_importance.csv` - 44 features ranked by coefficient magnitude
- `data_preparation_report.json` - Data prep metadata and VIF analysis
- `validation_plots/residual_analysis.png` - Diagnostic plots

**Source Code** (in `src/modeling/`):
- `prepare_training_data.py` (483 lines) - DataPreparator class
- `train_multi_state_model.py` (631 lines) - MultiStateModelTrainer class
- `analyze_population_density.py` (280 lines) - Population density analysis

### Model Loading

```python
import pickle
from pathlib import Path

# Load model artifact
model_path = Path('data/models/multi_state_model_v1.pkl')
with open(model_path, 'rb') as f:
    model_artifact = pickle.load(f)

# Extract components
pipeline = model_artifact['pipeline']  # StandardScaler + Ridge
feature_names = model_artifact['feature_names']  # 44 features
best_alpha = model_artifact['best_alpha']  # 1000
training_date = model_artifact['training_date']
```

### Required Features (44 total)

**Dispensary Characteristics** (1):
- `sq_ft` - Square footage (most important predictor!)

**State Indicators** (2):
- `is_FL` - Binary (1 for Florida, 0 for Pennsylvania)
- `is_PA` - Binary (1 for Pennsylvania, 0 for Florida)

**Multi-Radius Populations** (5):
- `pop_1mi`, `pop_3mi`, `pop_5mi`, `pop_10mi`, `pop_20mi`

**Competitor Counts** (5):
- `competitors_1mi`, `competitors_3mi`, `competitors_5mi`, `competitors_10mi`, `competitors_20mi`

**Market Saturation** (5):
- `saturation_1mi`, `saturation_3mi`, `saturation_5mi`, `saturation_10mi`, `saturation_20mi`

**Census Demographics** (10):
- `median_age`, `median_household_income`, `per_capita_income`
- `pct_bachelor_plus`, `bachelor_degree`, `graduate_degree`, `doctorate_degree`
- `population_density`, `total_population`, `tract_area_sqm`

**Distance-Weighted Competition** (1):
- `competition_weighted_20mi`

**Demographic Interactions** (3):
- `affluent_market_5mi` (high-income population within 5 miles)
- `educated_urban_score` (education × density)
- `age_adjusted_catchment_3mi` (median age × population 3mi)

**State Interactions** (10):
- `pop_5mi_FL`, `pop_5mi_PA`
- `pop_20mi_FL`, `pop_20mi_PA`
- `competitors_5mi_FL`, `competitors_5mi_PA`
- `saturation_5mi_FL`, `saturation_5mi_PA`
- `median_household_income_FL`, `median_household_income_PA`

**Derived Features** (2):
- `pct_bachelor_plus` (bachelor + graduate + doctorate degrees)
- Additional demographic calculations

---

## 🔧 Technical Architecture

### Recommended File Structure

```
src/
├── prediction/
│   ├── __init__.py
│   ├── predictor.py               # Core prediction logic
│   ├── feature_validator.py       # Input validation
│   ├── confidence_intervals.py    # Bootstrap CI calculation
│   └── feature_sensitivity.py     # Sensitivity analysis
├── terminal/
│   ├── __init__.py
│   ├── cli.py                     # Main CLI interface
│   ├── input_collector.py         # Interactive input collection
│   └── output_formatter.py        # Pretty-print results
└── validation/
    ├── __init__.py
    ├── insa_validator.py          # Validate against Insa actuals
    └── error_analysis.py          # Systematic bias detection
```

### Key Classes to Build

#### 1. `MultiStatePredictor`
```python
class MultiStatePredictor:
    """
    Load model and generate predictions with confidence intervals.
    """
    def __init__(self, model_path='data/models/multi_state_model_v1.pkl'):
        self.load_model(model_path)

    def predict(self, features_dict):
        """Generate visit prediction from feature dict"""

    def predict_with_confidence(self, features_dict, confidence=0.95):
        """Generate prediction with confidence interval"""

    def feature_importance_for_site(self, features_dict):
        """Show feature contributions for this specific site"""
```

#### 2. `FeatureValidator`
```python
class FeatureValidator:
    """
    Validate input features for correctness.
    """
    def validate_state(self, state):
        """Ensure state is FL or PA"""

    def validate_numeric_range(self, feature, value):
        """Check feature is within reasonable range"""

    def validate_completeness(self, features_dict):
        """Ensure all 44 features provided"""

    def auto_generate_state_interactions(self, features_dict, state):
        """Automatically set state interaction features"""
```

#### 3. `InteractiveCLI`
```python
class InteractiveCLI:
    """
    Terminal interface for predictions.
    """
    def collect_inputs(self):
        """Interactively collect all 44 features"""

    def display_prediction(self, result):
        """Pretty-print prediction with confidence interval"""

    def batch_mode(self, csv_path):
        """Process multiple sites from CSV"""

    def comparison_mode(self, sites_list):
        """Compare and rank multiple sites"""
```

---

## 📖 Reference: PA Dispensary Model Interface

The original PA model has a proven CLI interface we should adapt. Key features to replicate:

**Input Collection**:
- Interactive prompts for each feature
- Smart defaults based on typical ranges
- Validation with helpful error messages

**Output Format**:
```
============================================================
MULTI-STATE DISPENSARY VISIT PREDICTION
============================================================

Site Details:
  State: Florida
  Square Footage: 3,500 sq ft
  Population (5mi): 125,000
  Competitors (5mi): 6
  Market Saturation: 4.8 per 100k

Prediction:
  Expected Monthly Visits: 78,450 ± 12,300 (95% CI)
  Range: 66,150 - 90,750 visits/month

Feature Contributions:
  ✅ Square Footage: +10,325 visits (strong positive)
  ⚠️  Competition (5mi): -14,400 visits (high competition)
  ✅ Suburban Location: +4,585 visits (optimal density)
  ⚠️  Florida Market: -1,915 visits (lower baseline)

Confidence: MODERATE (R² = 0.19, similar sites in training data)

Recommendation: Consider this site - good size and location,
but monitor competitive landscape closely.
============================================================
```

---

## 🎯 Phase 4 Tasks Breakdown

### Task 1: Core Prediction Module (Week 1)
**Deliverable**: `src/prediction/predictor.py`

1. Load model artifact with error handling
2. Validate all 44 features present
3. Generate predictions via Pipeline
4. Implement bootstrap confidence intervals
5. Add feature contribution breakdown
6. Unit tests for prediction logic

**Acceptance Criteria**:
- Loads model successfully
- Generates predictions matching training script results
- 95% CI calculated via bootstrap (1000 iterations)
- All 44 features validated

### Task 2: Input Validation Module (Week 1)
**Deliverable**: `src/prediction/feature_validator.py`

1. Define reasonable ranges for each feature
2. State indicator validation (FL vs PA)
3. Auto-generate state interactions from base features
4. Completeness check (all 44 features)
5. Type validation (numeric, binary)
6. Unit tests for edge cases

**Acceptance Criteria**:
- Rejects invalid states
- Catches missing features
- Auto-generates 10 state interaction features
- Validates numeric ranges

### Task 3: Terminal Interface (Week 2)
**Deliverable**: `src/terminal/cli.py`

1. Interactive input collection (44 features)
2. Batch mode from CSV
3. Comparison mode (rank multiple sites)
4. Pretty-print output formatting
5. Error handling and help text
6. Integration tests

**Acceptance Criteria**:
- User can interactively enter all features
- CSV batch mode processes multiple sites
- Output matches PA model formatting
- Graceful error handling

### Task 4: Validation Against Insa Actuals (Week 3)
**Deliverable**: `src/validation/insa_validator.py`

1. Gather Insa actual performance data (FL, MA, CT stores)
2. Generate predictions for Insa locations
3. Calculate prediction errors (RMSE, MAE, MAPE)
4. Identify systematic biases (over/under prediction)
5. Analyze by state and store characteristics
6. Calibrate confidence intervals based on actual error

**Acceptance Criteria**:
- Predictions generated for all Insa stores
- Error metrics calculated and documented
- Bias patterns identified
- CI calibration recommendations provided

### Task 5: Documentation (Week 3)
**Deliverables**: Multiple docs

1. `USER_MANUAL.md` - How to use terminal interface
2. `MODEL_INTERPRETATION_GUIDE.md` - Business-friendly feature explanations
3. `LIMITATIONS.md` - Model boundaries and caveats
4. `DEPLOYMENT_GUIDE.md` - Installation and production setup

**Acceptance Criteria**:
- Non-technical user can follow manual
- Business users understand feature impacts
- Limitations clearly communicated
- Deployment process documented

---

## ⚠️ Important Considerations

### Model Limitations

**R² = 0.19 means**:
- Model explains ~19% of visit variance
- 81% remains unexplained (product mix, marketing, staff, etc.)
- Use for directional guidance, not precise forecasts
- Always provide confidence intervals

**State-Specific Performance**:
- Florida R² = 0.0493 (weaker predictions)
- Pennsylvania R² = -0.0271 (very weak, small sample)
- Overall performance drives utility, but flag uncertainty for PA

**Small PA Sample**:
- Only 30 PA test samples (121 training)
- PA predictions have higher uncertainty
- Consider wider confidence intervals for PA sites

### Feature Engineering Challenges

**Auto-Generating Features**:
- User provides base features (sq_ft, state, populations, competitors)
- System must auto-generate:
  - State indicators (is_FL, is_PA)
  - State interactions (pop_5mi_FL, competitors_5mi_PA, etc.)
  - Demographic interactions (affluent_market_5mi, educated_urban_score)

**Missing Features**:
- If user lacks census demographics, need reasonable defaults
- Consider using state-level medians from training data
- Flag predictions with defaulted features as "LOWER CONFIDENCE"

### Production Deployment

**Dependencies**:
```
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
```

**Environment**:
- Python 3.9+ required
- Model artifact size: 5.42 KB (portable)
- No external API calls needed for prediction
- Census data already embedded in features

---

## 🔍 Testing Strategy

### Unit Tests
- Prediction logic with known inputs
- Feature validation edge cases
- State interaction auto-generation
- Confidence interval calculation

### Integration Tests
- Full CLI workflow (input → prediction → output)
- Batch CSV processing
- Error handling for invalid inputs
- Model loading and feature alignment

### Validation Tests
- Insa actual vs predicted comparison
- Systematic bias detection
- Cross-state performance comparison
- Confidence interval coverage (should contain ~95% of actuals)

---

## 📚 Key Documentation References

**Model Performance**:
- `docs/PHASE3B_MODEL_TRAINING_COMPLETE.md` - Full Phase 3b report
- `docs/CODEX_REVIEW_DOUBLE_SCALING_FIX.md` - Critical bug fix details
- `data/models/model_performance_report.json` - Training metrics

**Feature Engineering**:
- `docs/PHASE3A_COMPETITIVE_FEATURES_COMPLETE.md` - Competitive features
- `docs/PHASE2_COMPLETION_REPORT.md` - Census demographics
- `data/models/feature_importance.csv` - Feature rankings

**Data Integration**:
- `docs/PHASE1_COMPLETION_REPORT.md` - Data sources and quality
- `data/processed/combined_with_competitive_features.csv` - Full dataset (78 cols)

**Project Guidelines**:
- `CLAUDE.md` - Project principles and data integrity standards
- `README.md` - Project overview and quick start

---

## 🚀 Quick Start for Phase 4

```bash
# 1. Navigate to project
cd /Users/daniel_insa/Claude/multi-state-dispensary-model

# 2. Verify model artifact exists
ls -lh data/models/multi_state_model_v1.pkl
# Should show: 5.42 KB file

# 3. Test model loading
python3 -c "import pickle; m = pickle.load(open('data/models/multi_state_model_v1.pkl', 'rb')); print(f'Model loaded: {len(m[\"feature_names\"])} features')"
# Should output: Model loaded: 44 features

# 4. Review feature names
python3 -c "import pickle; m = pickle.load(open('data/models/multi_state_model_v1.pkl', 'rb')); print('\n'.join(m['feature_names']))"

# 5. Check training report
cat data/models/model_performance_report.json | python3 -m json.tool | head -30

# 6. Review Phase 3b completion report
cat docs/PHASE3B_MODEL_TRAINING_COMPLETE.md | head -60

# 7. Create prediction module structure
mkdir -p src/prediction src/terminal src/validation

# 8. Start building predictor.py (see Task 1 above)
```

---

## 💡 Recommended Approach

### Week 1: Core Functionality
Focus on getting basic predictions working:
1. Build `MultiStatePredictor` class
2. Load model and generate single-site predictions
3. Implement feature validation
4. Add basic confidence intervals

### Week 2: User Interface
Build terminal interface:
1. Interactive CLI for input collection
2. Pretty-print output formatting
3. Batch CSV processing
4. Comparison mode

### Week 3: Validation & Documentation
Validate and document:
1. Test against Insa actual performance
2. Write user documentation
3. Create deployment guide
4. Finalize for production

---

## 📊 Expected Deliverables

### Code Deliverables
- `src/prediction/` - Prediction modules (3-4 files)
- `src/terminal/` - CLI interface (3 files)
- `src/validation/` - Validation modules (2 files)
- `tests/test_prediction.py` - Prediction tests
- `tests/test_terminal.py` - CLI tests

### Documentation Deliverables
- `USER_MANUAL.md` - Terminal interface guide
- `MODEL_INTERPRETATION_GUIDE.md` - Business guide
- `LIMITATIONS.md` - Model boundaries
- `DEPLOYMENT_GUIDE.md` - Production setup
- `PHASE4_COMPLETION_REPORT.md` - Phase 4 summary

### Validation Deliverables
- Insa validation report (predictions vs actuals)
- Error analysis and bias detection
- Confidence interval calibration
- Recommendations for model improvements

---

## 🎯 Success Metrics

**Functional Success**:
- ✅ Terminal interface generates predictions for any FL/PA site
- ✅ Batch mode processes 10+ sites in CSV format
- ✅ Confidence intervals calibrated to ~95% coverage
- ✅ User manual enables non-technical use

**Validation Success**:
- ✅ Insa actual vs predicted MAPE < 50%
- ✅ No systematic bias by state or store size
- ✅ Confidence intervals contain 90-95% of actual values
- ✅ Model limitations clearly documented

**Production Readiness**:
- ✅ Clean installation process documented
- ✅ Error handling prevents crashes
- ✅ Output format approved by business users
- ✅ Deployment guide enables production setup

---

## ⚡ Pro Tips

### Development Tips
1. **Start simple**: Get basic prediction working before adding features
2. **Test incrementally**: Unit test each component as you build
3. **Use real data**: Test with actual training data features to verify correctness
4. **Copy PA model patterns**: The PA model CLI is proven - adapt, don't reinvent

### Business Communication
1. **Always show uncertainty**: Confidence intervals are critical for trust
2. **Explain predictions**: Feature contributions help users understand
3. **Flag limitations**: Be upfront about model boundaries
4. **Actionable output**: Recommendations, not just numbers

### Model Usage
1. **Never extrapolate**: Stay within training data ranges
2. **Check feature alignment**: All 44 features must match training order
3. **Validate state interactions**: Auto-generate, don't ask user for them
4. **Monitor predictions**: Track actual vs predicted over time

---

## 📞 Questions to Resolve

Before starting Phase 4, clarify:

1. **Insa Actual Data Access**:
   - Which Insa stores do we have actual performance data for?
   - What format is the data in?
   - What time period should we use for validation?

2. **User Requirements**:
   - Who are the primary users? (site selection team, executives, analysts?)
   - Preferred input method? (interactive CLI, CSV batch, API?)
   - Output format preferences? (terminal, CSV, JSON, PDF report?)

3. **Deployment Environment**:
   - Where will this run? (local laptops, server, cloud?)
   - Any infrastructure constraints?
   - Update frequency needed?

4. **Feature Data Collection**:
   - How will users gather 44 features for new sites?
   - Can we simplify input (e.g., auto-fetch census data by address)?
   - Acceptable level of manual data entry?

---

## 🎬 Ready to Start?

**Phase 4 is ready to begin!** All prerequisites are in place:

✅ Model trained and validated (R² = 0.1940)
✅ Model artifact saved and portable (5.42 KB)
✅ All 44 features documented and ranked
✅ Critical bugs fixed and metrics validated
✅ Comprehensive documentation available
✅ Code pushed to Git and ready for Phase 4 development

**Next command after compacting**:
```bash
cd /Users/daniel_insa/Claude/multi-state-dispensary-model
cat docs/PHASE4_CONTINUATION_PROMPT.md
```

---

*Multi-State Dispensary Model - Phase 4 Continuation Prompt*
*Date: October 23, 2025*
*Status: Ready to Begin*
*Previous Phase: Phase 3b Complete ✅*
