# Continuation Prompt: Model Improvement Phase

**Date**: October 23, 2025
**Phase**: Model Improvement - Temporal Adjustments & Brand Effects
**Status**: Ready to Start
**Priority**: HIGH - Improve PA model from R² = -0.03 to 0.15+

---

## 📋 Quick Start (Copy/Paste This)

```
Let's continue work on the Multi-State Dispensary Model project.

We're starting the model improvement phase to boost predictive power from R² = 0.19 to 0.30+.

Navigate to: /Users/daniel_insa/Claude/multi-state-dispensary-model

Please read:
1. docs/MODEL_IMPROVEMENT_IDEAS.md - Full improvement roadmap
2. docs/MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md - Current performance baseline

Priority tasks:
1. PA temporal adjustments (annualize visits for sites < 12 months old)
2. Brand effects analysis (test if brand identity predicts performance)
3. Time-weighted competition metrics

Expected improvement: +0.10 to +0.15 R² (would achieve 0.29-0.34 overall)
```

---

## 🎯 Current State Summary

### Model Performance (Baseline)
- **Overall R²**: 0.194 (explains 19% of variance)
- **Florida R²**: 0.049 (very weak, but usable for comparison)
- **Pennsylvania R²**: -0.027 (doesn't work, worse than guessing average)

### What's Complete ✅
1. **Data Integration** - 741 training dispensaries, 937 total landscape
2. **Feature Engineering** - 44 features (demographics, competition, population)
3. **Model Training** - Ridge regression with state interactions
4. **Terminal Interface** - Interactive CLI and batch processing
5. **Documentation** - Comprehensive technical and executive summaries

### What's Next 🚧
**Priority 1: PA Temporal Adjustments**
- Many PA dispensaries opened < 1 year ago
- Current model treats partial-year data as full-year performance
- Solution: Annualize visits based on months operational
- Solution: Time-weight competition (competitor open 6 months = 0.5 weight)
- **Expected gain**: +0.05 to +0.08 R²

**Priority 2: Brand Effects**
- Test if Curaleaf, Trulieve, Cresco, etc. drive different visit volumes
- Create brand performance index or category flags
- **Expected gain**: +0.05 to +0.10 R²

**Priority 3: Traffic Data**
- Integrate DOT AADT (Annual Average Daily Traffic)
- Already planned in original scope
- **Expected gain**: +0.02 to +0.05 R²

---

## 📁 Key Files

### Documentation
- **MODEL_IMPROVEMENT_IDEAS.md** - Detailed improvement roadmap (this is the main document)
- **MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md** - Business stakeholder summary
- **PHASE3B_MODEL_TRAINING_COMPLETE.md** - Current model training results

### Code
- **src/modeling/train_multi_state_model.py** - Current training script
- **data/processed/combined_with_competitive_features.csv** - Training dataset (937 rows)

### Model Artifacts
- **data/models/multi_state_model_v1.pkl** - Current production model
- **data/models/training_report.json** - Performance metrics

---

## 🔑 Key Questions to Ask Daniel

Before starting implementation, confirm:

1. **PA Opening Dates**: Do we have PA dispensary opening dates already?
   - Check if in current dataset: `data/processed/combined_with_competitive_features.csv`
   - If not, need to scrape from PA Department of Health website

2. **Maturity Curve**: Do we have Insa's historical ramp-up data?
   - First 3, 6, 9, 12 months of performance for Insa stores
   - Would inform how to annualize partial-year performance
   - If not available, will use industry standard assumptions

3. **Brand Data**: Are brand names in Placer data?
   - Check column names in current dataset
   - May need to extract from `dba_name` or similar field
   - May need manual standardization (e.g., "Curaleaf Holdings LLC" → "Curaleaf")

4. **Success Criteria**: What's the minimum acceptable R²?
   - Current target: Overall 0.30+, PA 0.15+
   - Confirm this aligns with business needs

---

## 📊 Implementation Roadmap

### Session 1: Data Preparation (2-3 hours)
1. Check for PA opening dates in existing data
2. Extract and standardize brand names
3. Calculate months_operational for each dispensary
4. Create data quality report

### Session 2: Feature Engineering (2-3 hours)
1. Implement visit annualization for PA sites < 12 months
2. Create time-weighted competition metrics
3. Calculate brand performance indices
4. Validate new features against training data

### Session 3: Model Retraining (1-2 hours)
1. Retrain with temporal + brand features
2. Compare performance vs baseline (v1)
3. Analyze feature importance
4. Update confidence intervals if needed

### Session 4: Validation & Documentation (1-2 hours)
1. Test on holdout set
2. Validate PA performance improvement
3. Update MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md
4. Create v2 model artifact
5. Commit and document changes

**Total Estimated Time**: 6-10 hours across 2-3 sessions

---

## 🎯 Success Metrics

### Minimum Viable Improvement
- Overall R²: 0.19 → **0.25** (+31% improvement)
- PA R²: -0.03 → **0.05** (from broken to marginally useful)

### Target Performance
- Overall R²: 0.19 → **0.30** (+58% improvement)
- Florida R²: 0.05 → **0.15** (3x improvement)
- PA R²: -0.03 → **0.15** (from broken to usable)

### Stretch Goal
- Overall R²: 0.19 → **0.35** (+84% improvement)
- Florida R²: 0.05 → **0.20** (4x improvement)
- PA R²: -0.03 → **0.20** (from broken to good)

---

## ⚠️ Important Notes

### Don't Break Existing Functionality
- Terminal interface should work with v2 model (no API changes)
- Feature validator may need updates if adding required features
- Maintain backward compatibility with v1 for comparison

### Data Integrity Principles
- No synthetic data without explicit approval
- Document all assumptions (maturity curves, brand categorization)
- Validate temporal adjustments against known-good examples

### Testing Strategy
- Compare v2 vs v1 on same test set
- Leave-one-state-out validation (FL-only, PA-only training)
- Error analysis by subgroups (new vs mature sites, MSO vs independent)

---

## 📚 Reference Documents

**Must Read**:
1. **MODEL_IMPROVEMENT_IDEAS.md** - Detailed technical specs for all improvements
2. **PHASE3B_MODEL_TRAINING_COMPLETE.md** - How v1 model was trained

**Optional Context**:
3. **PHASE3A_COMPETITIVE_FEATURES_COMPLETE.md** - How competition features work
4. **CODEX_REVIEW_DOUBLE_SCALING_FIX.md** - Critical bug fix (avoid similar issues)
5. **MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md** - Business context

---

## 🚀 Quick Commands

```bash
# Navigate to project
cd /Users/daniel_insa/Claude/multi-state-dispensary-model

# Check for PA opening dates
python3 -c "import pandas as pd; df = pd.read_csv('data/processed/combined_with_competitive_features.csv'); print(df.columns.tolist())"

# Check for brand data
python3 -c "import pandas as pd; df = pd.read_csv('data/processed/combined_with_competitive_features.csv'); print([col for col in df.columns if 'name' in col.lower() or 'brand' in col.lower()])"

# Verify current model performance
python3 src/prediction/predictor.py
```

---

*Ready to improve the model from R² = 0.19 to 0.30+ through temporal adjustments and brand effects!*
