# Phase 6 Continuation Prompt - Model v2 Training

## Copy/Paste This After Compacting:

> **"Let's continue Phase 6: Train model v2 with corrected data. See docs/CONTINUATION_PROMPT_PHASE6_TRAINING.md for context."**

---

## Context: What's Been Completed

### Phase 6 Progress (Steps 1-4 Complete)

**✅ Step 1: Temporal Adjustment Discrepancy Resolved**
- Investigated 17 vs 15 site discrepancy
- Confirmed: 15 FL sites have temporal adjustments applied (not 17)
- Documentation updated to reflect correct count

**✅ Step 2: prepare_training_data.py Updated**
- Default dataset: `combined_with_competitive_features_corrected.csv`
- Default target: `corrected_visits` (ANNUAL visits)
- Added `target_column` parameter for flexibility
- **CRITICAL FIX**: Excluded `corrected_visits_step1` (prevented data leakage)
- All legacy columns excluded: `visits`, `visits_per_sq_ft`, `corrected_visits_per_sq_ft`

**✅ Step 3: train_multi_state_model.py Updated**
- Added `model_version` parameter (default='v2')
- Automatically uses corrected dataset and target for v2
- Model artifacts auto-versioned: `multi_state_model_v2.pkl`
- Training report auto-versioned: `multi_state_model_v2_training_report.json`
- Added metadata: `model_version`, `target_column`, `data_units='annual_visits'`

**✅ Step 4: CLI Updated for Annual Visits**
- All "visits/month" changed to "visits/year"
- Header shows model version and target column
- Prediction output: "Expected Annual Visits"
- Model info display updated for annual units

**✅ Codex Review Fixes Applied**
- Data leakage fix: `corrected_visits_step1` excluded from features
- Documentation: All "17 sites" corrected to "15 sites" (8 occurrences in PHASE5B, 3 in PHASE6)

---

## Current State

### Files Ready for Training

**Training Scripts** (Updated):
- `src/modeling/prepare_training_data.py` - Uses corrected dataset, excludes leakage columns
- `src/modeling/train_multi_state_model.py` - Configured for model v2

**Dataset** (Ready):
- `data/processed/combined_with_competitive_features_corrected.csv`
- 741 training dispensaries
- Target: `corrected_visits` (ANNUAL visits, Placer-corrected + temporal adjustments)
- 44 features (all safe, no data leakage)

**Interface** (Updated):
- `src/terminal/cli.py` - Annual visit labels throughout
- `src/prediction/predictor.py` - **NEEDS UPDATE** to load v2 model
- `src/prediction/feature_validator.py` - Ready (no changes needed)

**Documentation** (Current):
- All counts corrected (15 sites, not 17)
- Phase 6 progress documented
- Codex review fixes documented

---

## Next Steps (Phase 6 Continuation)

### Step 5: Train Model v2 ⏳ READY TO START

**Command**:
```bash
cd /Users/daniel_insa/Claude/multi-state-dispensary-model
python3 src/modeling/train_multi_state_model.py
```

**What Will Happen**:
1. Load corrected dataset (`corrected_visits` target)
2. Prepare 741 training dispensaries (44 features)
3. Train Ridge regression (alpha=1000, same as v1)
4. 5-fold cross-validation
5. Test set evaluation
6. State-specific performance (FL vs PA)
7. Feature importance analysis
8. Save model as `multi_state_model_v2.pkl`
9. Generate training report

**Expected Duration**: ~2-5 minutes

**Expected Metrics**:
- R² may be similar to v1 (~0.18-0.20)
- BUT predictions will match reality (no 45% overestimate)
- Absolute accuracy should be 45% better when validated against Insa

---

### Step 6: Update predictor.py ⏳ PENDING

**Changes Needed**:
- Change default model path from `v1.pkl` to `v2.pkl`
- Verify model metadata is read correctly
- No need to convert units (model already in annual)
- Update docstrings to clarify annual predictions

**Files to Modify**:
- `src/prediction/predictor.py`

---

### Step 7: Update test_cli.py ⏳ PENDING

**Changes Needed**:
- Update test expectations from monthly to annual
- Multiply expected values by 12 (or update test data)
- Verify batch processing tests

**Files to Modify**:
- `test_cli.py`

---

### Step 8: Compare v1 vs v2 Performance ⏳ PENDING

**Create Comparison Report**:
- R² scores (cross-val and test)
- RMSE (should be ~45% lower for v2 in absolute terms)
- Feature importance changes
- Validation against Insa (v1 overestimates by 45%, v2 should be within 20%)

**Create**:
- `docs/MODEL_V1_VS_V2_COMPARISON.md`

---

### Step 9: Create Phase 6 Documentation ⏳ PENDING

**Document**:
- Model v2 training results
- Performance comparison (v1 vs v2)
- Validation against Insa actual
- Key insights and recommendations

**Create**:
- `docs/PHASE6_MODEL_V2_COMPLETE.md`

**Update**:
- `README.md` - Phase 6 status complete
- `MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md` - v2 results

---

## Critical Reminders

### Data Leakage - FIXED ✅
All target-related columns excluded:
- ✅ `corrected_visits` (target itself)
- ✅ `corrected_visits_step1` (intermediate step - **critical fix**)
- ✅ `corrected_visits_per_sq_ft` (derived from target)
- ✅ `visits` (uncorrected legacy)
- ✅ `visits_per_sq_ft` (uncorrected legacy)

### Temporal Adjustments - CORRECTED ✅
- Actual count: **15 sites** (not 17)
- All documentation updated
- Average months operational: 7.8
- Range: 2.6 to 11.4 months

### Units - ANNUAL ✅
- Target: `corrected_visits` is ANNUAL visits
- Model predictions: ANNUAL visits
- CLI displays: ANNUAL visits ("visits/year")
- No conversion needed in predictor

---

## Success Criteria

### Technical
- ✅ Model v2 trains successfully
- ✅ No data leakage warnings
- ✅ R² ≥ 0.18 (maintain v1 performance)
- ✅ All 44 features used correctly

### Business Validation
- ✅ Predictions within 20% of Insa actual (vs 45% overestimate for v1)
- ✅ Confidence intervals properly scaled
- ✅ Stakeholders trust predictions

### Documentation
- ✅ Comprehensive training report
- ✅ v1 vs v2 comparison
- ✅ Clear explanation for stakeholders
- ✅ Validation against real performance

---

## Key Files & Locations

### Training
- Script: `src/modeling/train_multi_state_model.py`
- Dataset: `data/processed/combined_with_competitive_features_corrected.csv`
- Model output: `data/models/multi_state_model_v2.pkl`
- Report output: `data/models/multi_state_model_v2_training_report.json`

### Interface
- CLI: `src/terminal/cli.py` (updated ✅)
- Predictor: `src/prediction/predictor.py` (needs update ⏳)
- Validator: `src/prediction/feature_validator.py` (ready ✅)

### Documentation
- Phase 5b: `docs/PHASE5B_CORRECTIONS_COMPLETE.md` (corrected ✅)
- Phase 6: `docs/CONTINUATION_PROMPT_PHASE6.md` (corrected ✅)
- Codex fixes: `docs/CODEX_REVIEW_PHASE6_FIXES.md` (complete ✅)
- Next: `docs/PHASE6_MODEL_V2_COMPLETE.md` (to create ⏳)

---

## Quick Start Commands

```bash
# Navigate to project
cd /Users/daniel_insa/Claude/multi-state-dispensary-model

# Verify dataset
python3 -c "
import pandas as pd
df = pd.read_csv('data/processed/combined_with_competitive_features_corrected.csv')
print(f'Training sites: {df[\"has_placer_data\"].sum()}')
print(f'Target: corrected_visits (ANNUAL)')
print(f'Mean annual visits: {df[df[\"has_placer_data\"]==True][\"corrected_visits\"].mean():,.0f}')
"

# Train model v2
python3 src/modeling/train_multi_state_model.py

# After training completes, test CLI
python3 src/terminal/cli.py
```

---

**Ready to train model v2 with corrected, calibrated annual visit data!**

*Phase 6 Steps 1-4 complete. Ready for Step 5: Model Training.*
