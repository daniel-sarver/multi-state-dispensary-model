# Continuation Prompt - Building State-Specific Models v3.0

**Date**: October 28, 2025
**Status**: Ready to build separate FL and PA models
**Estimated Time**: 2 hours for comprehensive feature selection testing

---

## Context: What We Discovered

User's actual use case: **Compare sites WITHIN states** (FL vs FL, PA vs PA)

**Problem**: Current model v2 optimized for WRONG use case
- Overall R² = 0.19 is inflated by between-state differences
- Within-state R² is very weak:
  - Florida: R² = 0.048 (explains only 4.8% of variance)
  - Pennsylvania: R² = -0.028 (negative = worse than guessing)

**Root cause**: Demographics and competition features have almost no signal within individual states
- FL best feature: competitors_5mi explains only 5.7% of variance
- PA best feature: competitors_20mi explains only 12.8% of variance

**Full diagnostic analysis**: `docs/WITHIN_STATE_PREDICTION_ANALYSIS.md`

---

## Task: Build State-Specific Models with Feature Selection

### Objective
Train separate FL-only and PA-only models to maximize within-state predictive power

### Approach: Comprehensive Feature Selection (Option 2 - 2 hours)

For each state, test 5 feature combinations:

#### Florida Feature Sets:
1. **Full model** (44 features) - baseline
2. **Competition-focused** - Short radius (1mi, 3mi, 5mi competitors + saturation)
3. **Demographics-focused** - Population + income + education (no competition)
4. **Best-of-both** - Top competition features + top demographic features
5. **Minimal model** - Only competitors_5mi + sq_ft + pop_5mi

#### Pennsylvania Feature Sets:
1. **Full model** (44 features) - baseline
2. **Competition-focused** - Long radius (10mi, 20mi competitors + saturation)
3. **Demographics-focused** - Population + income + education (no competition)
4. **Best-of-both** - Top competition features + top demographic features
5. **Minimal model** - Only competitors_20mi + sq_ft + pop_20mi

### Algorithms to Test:
- Ridge Regression (baseline)
- Random Forest (capture non-linear relationships)
- XGBoost (gradient boosting)

### Evaluation:
- 5-fold cross-validation within state
- Compare within-state R² scores
- Select best combination for each state

---

## Implementation Plan

### Phase 1: Create State-Specific Training Script (30 min)
**File**: `src/modeling/train_state_specific_models.py`

**Tasks**:
1. Load training data and split by state
2. Define 5 feature combinations per state
3. Test each combination with Ridge/RF/XGBoost
4. Generate performance comparison report
5. Save best model for each state

**Outputs**:
- `data/models/fl_model_v3.pkl` - Best FL model
- `data/models/pa_model_v3.pkl` - Best PA model
- `data/models/fl_training_report_v3.json` - FL results
- `data/models/pa_training_report_v3.json` - PA results
- `analysis_output/state_models_v3/comparison_report.txt`

---

### Phase 2: Update Prediction Module (15 min)
**File**: `src/modeling/predictor.py`

**Change**: Route to state-specific model based on user's state selection

```python
def load_model(state):
    """Load state-specific model."""
    if state == 'FL':
        return joblib.load('data/models/fl_model_v3.pkl')
    elif state == 'PA':
        return joblib.load('data/models/pa_model_v3.pkl')
```

**User impact**: ZERO - CLI workflow unchanged

---

### Phase 3: Testing (30 min)
**Tasks**:
1. Test FL predictions with known sites
2. Test PA predictions with known sites
3. Verify within-state R² improvement
4. Validate CLI still works identically
5. Compare predictions v2 vs v3

---

### Phase 4: Documentation (30 min)
**Tasks**:
1. Update `MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md` with v3 results
2. Create `docs/PHASE7_STATE_SPECIFIC_MODELS_V3.md` with full training report
3. Update CONTINUE.txt with v3 deployment status
4. Create session summary document

---

## Expected Outcomes

### Best Case Scenario:
- FL within-state R² improves from 0.048 → 0.10-0.15
- PA within-state R² improves from -0.028 → 0.10-0.20
- Clear feature insights (e.g., "FL success driven by local competition, PA by regional saturation")

### Realistic Scenario:
- Small improvement (R² +0.02 to +0.05)
- Confirms feature limitation, not model architecture issue
- Provides empirical evidence for next steps (AADT integration or accept limitations)

### Worst Case Scenario:
- No improvement over v2
- Definitively proves we need better features (operational data, AADT, etc.)
- Guides decision to pursue Option C (AADT) or Option D (operational data)

---

## Key Files Reference

### Analysis Outputs:
- `analysis_output/state_diagnostics/FL_feature_correlations.csv` - All FL feature correlations
- `analysis_output/state_diagnostics/PA_feature_correlations.csv` - All PA feature correlations
- `analysis_output/state_diagnostics/FL_top_features.png` - Visualization
- `analysis_output/state_diagnostics/PA_top_features.png` - Visualization

### Code Files to Modify:
- `src/modeling/train_state_specific_models.py` (NEW - create this)
- `src/modeling/predictor.py` (MODIFY - add state routing)

### Documentation to Update:
- `docs/MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md`
- `CONTINUE.txt`

---

## Important Notes

### Data Leakage Check: ✅ VERIFIED CLEAN
Model code properly excludes:
- `visits_per_sq_ft`
- `corrected_visits_per_sq_ft`
- `corrected_visits_step1`

No data leakage in training pipeline.

### Training Data:
- Florida: 590 dispensaries (sufficient for separate model)
- Pennsylvania: 151 dispensaries (smaller, may benefit from simpler model)

### User Experience:
CLI workflow stays IDENTICAL:
1. Select state → FL or PA
2. Enter coordinates
3. Enter square footage
4. Enter address (optional)
5. Enter AADT (optional)

System automatically loads correct state model behind the scenes.

---

## Success Criteria

### Minimum Success:
- Both state models train without errors
- Within-state R² ≥ current v2 performance
- CLI works identically from user perspective

### Target Success:
- FL within-state R² > 0.10
- PA within-state R² > 0.10
- Clear feature insights for each state

### Stretch Success:
- FL within-state R² > 0.15
- PA within-state R² > 0.20
- Significantly improved site ranking accuracy

---

## If Feature Selection Doesn't Help

**Next Steps** (from WITHIN_STATE_PREDICTION_ANALYSIS.md):

1. **Option C: AADT Integration** (1-2 weeks)
   - Gather AADT data for all 741 training dispensaries
   - Expected improvement: R² +0.03 to +0.07

2. **Option D: Operational Data** (4-8 weeks)
   - Collect Insa operational data (product mix, staff, marketing)
   - Expected improvement: R² +0.15 to +0.30

3. **Accept Limitations**
   - Use model for initial screening only
   - Weight local market intelligence heavily (60%+)
   - Acknowledge predictions have ±50-75% error

---

## Ready to Start

All diagnostic work complete. Training data prepared. Feature correlations analyzed.

**Next step**: Create `src/modeling/train_state_specific_models.py` and begin comprehensive feature selection testing.
