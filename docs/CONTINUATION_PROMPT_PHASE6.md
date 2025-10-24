# Phase 6 Continuation Prompt

## Copy/Paste This After Compacting:

> **"Phase 5b is complete. Let's begin Phase 6: Retrain model v2 using the corrected_visits target variable. See docs/CONTINUATION_PROMPT_PHASE6.md for context."**

---

## Context for Phase 6: Model v2 Training

### What Was Accomplished in Phase 5b

**Phase 5b successfully implemented two major data corrections:**

1. **Placer Calibration Correction**
   - Discovered Placer data represents ANNUAL visits (not monthly)
   - Used 7 Insa FL stores to calculate correction factor: 0.5451
   - Placer overestimates visits by 45.5%
   - Applied correction to all 741 training dispensaries

2. **FL Temporal Adjustments**
   - Parsed 59 FL recent openings (Oct 2024 - Oct 2025)
   - Matched 17 dispensaries <12 months operational
   - Applied maturity curve (30% → 100% over 12 months)
   - Annualized performance for sites not yet at steady-state

**Overall Impact:**
- Mean annual visits: 71,066 → 38,935 (-45.2% reduction)
- Created corrected dataset: `data/processed/combined_with_competitive_features_corrected.csv`

### Critical Naming Convention

**IMPORTANT - Use these column names:**
- `placer_visits`: Original Placer ANNUAL estimates (UNCORRECTED - for reference only)
- `corrected_visits`: ANNUAL visits after corrections (**USE THIS FOR MODEL V2**)
- `corrected_visits_per_sq_ft`: Efficiency metric (corrected)

**⚠️ All "visits" metrics are ANNUAL, not monthly**

---

## Phase 6 Objectives

### 1. Retrain Model v2 with Corrected Data

**Primary Task**: Train new model using `corrected_visits` as target variable

**Key Changes from v1:**
```python
# v1 used:
y = df['visits']  # or df['placer_visits']

# v2 should use:
y = df['corrected_visits']  # Corrected ANNUAL visits
```

**Expected Files to Modify:**
- `src/modeling/train_multi_state_model.py`
- Update target column parameter
- Generate new model artifact: `multi_state_model_v2.pkl`

### 2. Compare v1 vs v2 Performance

**Comparison Metrics:**
- **R² (Cross-Validation)**: May be similar (both explain variance in their respective targets)
- **Absolute Prediction Accuracy**: Should be MUCH better (v2 matches reality, v1 overestimates by 45%)
- **Validation Against Insa**: v2 should match Insa actual performance closely

**Why This Matters:**
- v1 R² = 0.1876 measures explained variance in UNCORRECTED target
- v2 R² = ? measures explained variance in CORRECTED target
- Even if R² similar, v2 predictions will be 45% more accurate in absolute terms

### 3. Update Terminal Interface for v2

**Required Changes:**
- Load `multi_state_model_v2.pkl` instead of v1
- Update output labels: "Predicted Annual Visits (Corrected)" not "Placer Visits"
- Recalculate RMSE for confidence intervals using v2 test set errors
- Update feature importance analysis

**Files to Modify:**
- `src/prediction/predictor.py`
- `src/terminal/cli.py`
- Update any hardcoded model paths or metric references

### 4. Documentation Updates

**Create:**
- `docs/PHASE6_MODEL_V2_COMPLETE.md` (comprehensive report)
- Model comparison table (v1 vs v2 performance)
- Validation report against Insa actual performance

**Update:**
- `README.md` (Phase 6 status, model v2 results)
- `docs/README.md` (add Phase 6 documentation)
- `MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md` (v2 results for stakeholders)

---

## Key Technical Details

### Model Training Configuration

**Recommended Approach** (same as v1 for fair comparison):
- Model: Ridge regression with alpha=1000
- Features: Same 44 features as v1 (for direct comparison)
- Cross-validation: 5-fold CV
- Test set: Same split as v1 (for fair comparison)
- State interactions: Include FL vs PA state terms

### Expected Results

**Conservative Estimate:**
- R² may not change significantly (0.18-0.20 range)
- But predictions will match reality (no 45% overestimate)
- Confidence intervals correctly scaled

**Optimistic Estimate:**
- If Placer bias varied systematically with features, R² could improve
- Potential R² improvement: +0.02 to +0.05
- Example: If Placer overestimated small stores more than large stores

**Guaranteed Improvement:**
- Predictions will match Insa actual performance
- Business stakeholders will trust the model
- No systematic 45% overestimation

### Validation Against Insa Stores

**Test Predictions Against:**
- 7 matched Insa stores used for calibration (should match closely)
- 3 unmatched Insa stores (independent validation)
- Compare predicted vs actual April 2025 monthly transactions

**Expected Validation Results:**
- v1: Predicts ~45% too high vs Insa actual
- v2: Predicts within 10-20% of Insa actual (typical model error)

---

## Data Files Ready to Use

### Primary Training Dataset
**Path**: `data/processed/combined_with_competitive_features_corrected.csv`

**Key Columns:**
- `corrected_visits`: Target variable for model v2 (ANNUAL, corrected)
- All feature columns from v1 (unchanged)
- `temporal_adjustment_applied`: Boolean flag (17 FL sites)
- `months_operational_at_collection`: Months open as of Oct 23, 2025
- `maturity_factor`: Maturity curve factor used
- `correction_placer_factor`: 0.5451 for all training sites

**Training Data:**
- 741 dispensaries with `has_placer_data=True`
- 590 FL, 151 PA
- 17 FL sites have temporal adjustments applied

### Model v1 for Comparison
**Path**: `data/models/multi_state_model_v1.pkl`

**Performance:**
- R² = 0.1876 (cross-val), 0.1940 (test)
- RMSE (FL): 33,162, RMSE (PA): 56,581
- 2.62x improvement over baseline (0.0716)

### Training Report v1
**Path**: `data/models/multi_state_model_v1_training_report.json`

Contains metrics, feature importance, and validation results from v1

---

## Success Criteria for Phase 6

### Required Deliverables
1. ✅ Trained model v2 artifact (`multi_state_model_v2.pkl`)
2. ✅ Training report v2 with performance metrics
3. ✅ Comparison report (v1 vs v2)
4. ✅ Validation report against Insa actual data
5. ✅ Updated terminal interface using v2
6. ✅ Updated documentation (README, Phase 6 report, executive summary)

### Performance Targets
- **Absolute Accuracy**: Predictions within 20% of Insa actual performance
- **R²**: Target ≥ 0.18 (maintain or improve v1 performance)
- **Business Validation**: Stakeholders trust predictions match reality
- **Cross-State Performance**: Similar performance in FL and PA

### Quality Standards
- Same test set split as v1 (for fair comparison)
- Comprehensive error analysis (residuals, outliers)
- Clear documentation of methodology
- Production-ready code with error handling

---

## Important Reminders

### Naming Convention (CRITICAL)
**Always use these exact column names:**
- `placer_visits`: UNCORRECTED (reference only, do NOT use for training)
- `corrected_visits`: CORRECTED (**USE THIS** for model v2 training)

**All "visits" are ANNUAL, not monthly**

### Data Corrections Already Applied
✅ Placer correction (0.5451 factor) - applied to all 741 training sites
✅ FL temporal adjustments - applied to 17 sites <12 months operational
✅ Naming convention - `placer_visits` vs `corrected_visits` clearly separated

**DO NOT re-apply corrections** - they're already in the dataset

### Files Created in Phase 5b
- `src/modeling/extract_insa_data.py` (192 lines)
- `src/modeling/apply_corrections.py` (488 lines)
- `data/processed/combined_with_competitive_features_corrected.csv` (corrected dataset)
- `docs/PHASE5B_CORRECTIONS_COMPLETE.md` (comprehensive documentation)

---

## Suggested First Steps

1. **Load corrected dataset** and verify `corrected_visits` column exists
2. **Check data quality** (741 training sites, no NaN in corrected_visits)
3. **Review v1 training script** (`src/modeling/train_multi_state_model.py`)
4. **Update target column** from `visits`/`placer_visits` → `corrected_visits`
5. **Train model v2** with same configuration as v1 (fair comparison)
6. **Compare performance** (R², RMSE, feature importance)
7. **Validate against Insa** (7 matched stores + 3 unmatched)

---

## Questions to Consider

- Should we use the exact same test set split as v1? (Recommended: YES for fair comparison)
- Should we try alternative models (Random Forest, XGBoost)? (Recommended: AFTER establishing Ridge v2 baseline)
- Should we adjust any hyperparameters? (Recommended: Start with alpha=1000 like v1)
- Should we add any new features? (Recommended: NO for v1 vs v2 comparison, maybe later in v3)

---

*This continuation prompt provides complete context for Phase 6 model v2 training after Phase 5b data corrections.*
