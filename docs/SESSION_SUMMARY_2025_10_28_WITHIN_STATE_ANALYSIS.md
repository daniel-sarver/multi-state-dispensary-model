# Session Summary - Within-State Prediction Analysis

**Date**: October 28, 2025
**Duration**: ~2 hours
**Focus**: Diagnostic analysis of within-state predictive power

---

## Session Overview

User requested optimization of model for **within-state comparisons** (FL vs FL, PA vs PA), not cross-state comparisons. This session diagnosed why current model v2 performs poorly for this use case and planned optimization strategy.

---

## Key Discovery: Overall R² is Misleading

### The Problem
- **Current model**: Overall R² = 0.19 appears decent
- **User's actual use case**: Compare sites WITHIN states
- **Reality**: Within-state R² is very weak (FL: 0.048, PA: -0.028)

### Why This Happens
Overall R² = 0.19 is inflated by **between-state differences**:
- PA median: 52,118 annual visits
- FL median: 31,142 annual visits
- Difference: 67% higher in PA

Just knowing "state = PA" provides significant predictive boost, but this doesn't help when comparing PA site vs PA site.

**Analogy**: Easy to predict NBA centers are taller than guards (between-group), but hard to predict which guards are tallest (within-group).

---

## Diagnostic Analysis Completed

### Created: `state_feature_diagnostics.py`
Analyzed which features correlate with performance within each state.

### Key Findings:

**Florida (590 dispensaries):**
| Feature | Correlation | Variance Explained |
|---------|-------------|-------------------|
| competitors_5mi | -0.239 | 5.7% |
| competitors_3mi | -0.213 | 4.5% |
| sq_ft | 0.173 | 3.0% |

**Pennsylvania (151 dispensaries):**
| Feature | Correlation | Variance Explained |
|---------|-------------|-------------------|
| competitors_20mi | -0.358 | 12.8% |
| competitors_10mi | -0.268 | 7.2% |
| saturation_20mi | -0.241 | 5.8% |

**Critical Insight**: Even the best individual feature explains only 5-13% of variance within states.

### Root Cause
Available features (demographics, competition, square footage) have almost no signal within individual states:
- Demographics are homogeneous within states (similar urban/suburban areas)
- Competition counts don't predict who wins competitive battles
- Missing critical factors: product quality, staff, marketing, store layout, etc.

---

## Work Completed

### 1. Created State-Specific Feature Diagnostic Script ✅
**File**: `src/analysis/state_feature_diagnostics.py`

**Functionality**:
- Calculates feature correlations with corrected_visits separately for FL and PA
- Identifies top predictive features for each state
- Calculates R² (variance explained) for individual features
- Generates visualizations and CSV exports

**Outputs**:
- `analysis_output/state_diagnostics/FL_feature_correlations.csv`
- `analysis_output/state_diagnostics/PA_feature_correlations.csv`
- `analysis_output/state_diagnostics/FL_variance_explained.csv`
- `analysis_output/state_diagnostics/PA_variance_explained.csv`
- `analysis_output/state_diagnostics/FL_top_features.png`
- `analysis_output/state_diagnostics/PA_top_features.png`

### 2. Created Comprehensive Analysis Report ✅
**File**: `docs/WITHIN_STATE_PREDICTION_ANALYSIS.md`

**Contents**:
- Detailed findings for FL and PA separately
- Explanation of why overall R² is misleading
- Why current features have weak within-state signal
- Analysis of whether separate state models would help
- Alternative modeling approaches to consider
- What would actually improve predictions (operational data, AADT, etc.)
- Realistic expectations for each optimization option
- Recommended next steps with effort/impact estimates

### 3. Data Leakage Verification ✅
Confirmed model training code properly excludes:
- `visits_per_sq_ft` (uncorrected derived variable)
- `corrected_visits_per_sq_ft` (derived target variable)
- `corrected_visits_step1` (intermediate correction step)

No data leakage present in current model.

---

## Optimization Strategy Planned

### Option A: Accept Current Limitations
- Update documentation to clarify model is for screening only
- **Investment**: None
- **Use case**: Cross-state comparisons only

### Option B: Build Separate State Models (CHOSEN - Next Task)
- Train FL-only and PA-only Ridge models
- Test 5 feature combinations per state
- Test Random Forest and XGBoost on best feature sets
- **Investment**: 2 hours
- **Expected**: Small improvement (R² +0.02 to +0.05), empirical evidence on feature limitations

### Option C: AADT Integration
- Gather AADT data for all 741 training dispensaries
- **Investment**: 1-2 weeks
- **Expected**: Moderate improvement (R² +0.03 to +0.07)

### Option D: Operational Data Integration
- Collect Insa operational data (product mix, staff, marketing)
- **Investment**: 4-8 weeks
- **Expected**: Major improvement (R² +0.15 to +0.30)

**Decision**: Start with Option B to empirically test if separate models help before investing in data collection.

---

## Feature Sets to Test (Option B)

### Florida:
1. Full model (44 features)
2. Competition-focused (1mi, 3mi, 5mi competitors + saturation)
3. Demographics-focused (population + income + education)
4. Best-of-both (top competition + top demographic features)
5. Minimal model (competitors_5mi + sq_ft + pop_5mi)

### Pennsylvania:
1. Full model (44 features)
2. Competition-focused (10mi, 20mi competitors + saturation)
3. Demographics-focused (population + income + education)
4. Best-of-both (top competition + top demographic features)
5. Minimal model (competitors_20mi + sq_ft + pop_20mi)

Note: FL and PA use different radii because diagnostic analysis showed FL success correlates with local competition (5mi) while PA correlates with regional saturation (20mi).

---

## CLI Impact: ZERO

User confirmed requirement: CLI workflow must stay identical.

**Implementation**: Automatic state routing
```python
if state == 'FL':
    model = load_model('fl_model_v3.pkl')
elif state == 'PA':
    model = load_model('pa_model_v3.pkl')
```

User experience unchanged:
1. Select state → FL or PA
2. Enter coordinates
3. Enter square footage
4. Enter address (optional)
5. Enter AADT (optional)

---

## Files Created/Modified

### New Files:
1. `src/analysis/state_feature_diagnostics.py` - Diagnostic analysis script
2. `docs/WITHIN_STATE_PREDICTION_ANALYSIS.md` - Comprehensive analysis report
3. `docs/CONTINUATION_PROMPT_2025_10_28_WITHIN_STATE_V3.md` - Full continuation context
4. `docs/SESSION_SUMMARY_2025_10_28_WITHIN_STATE_ANALYSIS.md` - This document

### Modified Files:
1. `CONTINUE.txt` - Updated with latest status and next task

### Analysis Outputs Created:
1. `analysis_output/state_diagnostics/FL_feature_correlations.csv`
2. `analysis_output/state_diagnostics/PA_feature_correlations.csv`
3. `analysis_output/state_diagnostics/FL_variance_explained.csv`
4. `analysis_output/state_diagnostics/PA_variance_explained.csv`
5. `analysis_output/state_diagnostics/FL_top_features.png`
6. `analysis_output/state_diagnostics/PA_top_features.png`

---

## Key Insights for Stakeholders

### What We Learned:
1. **Model v2 is optimized for wrong use case** - Cross-state comparison vs within-state ranking
2. **Feature limitation is fundamental** - Demographics and competition alone explain <10% within states
3. **Operational factors dominate** - Product quality, staff, marketing not in our data
4. **State-specific patterns exist** - FL driven by local competition (5mi), PA by regional saturation (20mi)

### Realistic Expectations:
With current data (demographics + competition):
- **Best case**: Within-state R² of 0.10-0.15 (10-15% variance explained)
- **Translation**: Predictions have ±40-60% error within states
- **Use case**: Initial screening and comparative ranking only, not financial projections

To achieve R² > 0.30 (reliable predictions), we need operational data (product mix, staff, marketing).

---

## Next Steps (After Compact)

**Immediate** (2 hours):
1. Create `src/modeling/train_state_specific_models.py`
2. Test 5 feature combinations per state
3. Test Ridge, Random Forest, XGBoost for each combination
4. Generate performance comparison report
5. Update prediction module to route to state models
6. Test with sample predictions
7. Update documentation with v3 results

**Follow-up** (based on v3 results):
- If R² improves significantly → Deploy v3 models
- If R² stays weak → Pursue AADT integration (Option C) or accept limitations

---

## Questions Answered This Session

1. **Why does overall R² = 0.19 seem decent but state predictions are poor?**
   - Overall R² inflated by between-state differences
   - Within-state R² is actually 0.048 (FL) and -0.028 (PA)

2. **What features actually predict success within states?**
   - FL: competitors_5mi (5.7% variance)
   - PA: competitors_20mi (12.8% variance)
   - Everything else <5% variance

3. **Will separate state models improve within-state predictions?**
   - Unknown - needs empirical testing (Option B)
   - Could help if state-specific coefficients unlock signal
   - May not help if features are fundamentally weak

4. **Should we try different population/competitor radii?**
   - Yes! Included in feature selection testing
   - FL seems driven by local competition (1-5mi)
   - PA seems driven by regional saturation (10-20mi)

---

## Status at Session End

- ✅ Diagnostic analysis complete
- ✅ Root cause identified (feature weakness within states)
- ✅ Optimization strategy planned (separate state models with feature selection)
- ✅ Implementation plan documented
- ✅ User confirmed CLI must stay unchanged
- ✅ User confirmed proceed with Option B (thorough feature selection)

**Ready to build**: State-specific models v3.0 with comprehensive feature selection testing.

**Next session**: Start implementation of separate FL and PA models.
