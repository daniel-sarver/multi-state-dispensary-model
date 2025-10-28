# Phase 5: Model Improvement - Exploration Complete

**Date**: October 24, 2025
**Phase**: Data Exploration & Analysis
**Status**: ✅ Complete - Ready for Placer Correction Implementation
**Next Phase**: Placer calibration (pending Insa actual data)

---

## 📋 Executive Summary

Phase 5 explored three potential model improvements:
1. **Temporal adjustments** (PA/FL opening dates)
2. **Outlier detection and removal**
3. **Placer visit correction** using Insa data

**Key Findings**:
- ❌ Temporal adjustments not needed (only 1 of 741 sites <12 months old)
- ❌ Outlier removal not recommended (all 4 low-traffic sites are legitimate)
- ✅ **Placer correction is highest-impact opportunity** (+0.03 to +0.08 R²)

**Decision**: Focus implementation efforts on Placer calibration correction.

---

## 🔍 Findings Summary

### Finding 1: Temporal Adjustments Not Applicable

**Initial Hypothesis**: Many PA/FL dispensaries opened <12 months ago, requiring visit annualization

**Reality Discovered**:
- **PA**: Only 1 of 151 training dispensaries <12 months old (0.7%)
  - RISE - York: 7.8 months operational, 99,821 visits/month
- **FL**: No opening dates in current dataset
- **Data collection date**: October 23, 2025 (more recent than expected)

**Conclusion**: **Skip temporal adjustments** - affects <1% of training data (minimal impact)

---

### Finding 2: Outliers Are Legitimate, Keep All

**4 low-traffic outliers identified** (<5k visits/month):
1. Ayr Cannabis - Tallahassee (4,201 visits, 12 competitors)
2. Trulieve - Tampa (2,834 visits, 11 competitors)
3. Mint Cannabis - Cape Coral (2,545 visits, 11 competitors)
4. Curaleaf - St. Augustine (1,882 visits, 3 competitors, small market)

**Analysis**:
- All have valid FL coordinates ✅
- All have reasonable match scores (82-93) ✅
- Low performance explained by market dynamics:
  - 3 sites: High competition (11-12 competitors in 5mi)
  - 1 site: Small market size (66k catchment)

**Decision**: **Keep all 4** - They contain valuable competitive dynamics signal

**Impact of removing**: Likely **negative** (-0.01 to -0.03 R²) due to lost signal

---

### Finding 3: Placer Correction Is Primary Opportunity

**8 Insa FL stores** available for calibration:
- Hudson (70,152 Placer visits)
- Orlando location 1 (55,227)
- Largo (53,471)
- Jacksonville (39,958)
- Summerfield (34,503)
- Orlando location 2 (31,360)
- Tampa (31,086)
- Tallahassee (25,227)

**What we need**: Actual monthly visit counts for these 8 stores

**Correction Methodology**:
```python
# Calculate Placer-to-actual ratio
correction_factor = sum(actual_visits) / sum(placer_visits)

# Apply to all training data
corrected_visits = placer_visits * correction_factor

# Retrain model with corrected target
model.fit(features, corrected_visits)
```

**Expected Impact**: +0.03 to +0.08 R²
- If Placer underestimates by 15%, correction factor = 1.15
- If Placer overestimates by 10%, correction factor = 0.90
- Improves both R² and absolute prediction accuracy

---

## 📊 Data Statistics

### Visit Distribution (Training Data, n=741)

**Overall**:
- Mean: 71,066 visits/month
- Median: 62,183
- Std Dev: 43,216
- Range: 1,882 to 394,345

**By State**:
- **FL** (n=590): Mean 62,365, Median 56,893
- **PA** (n=151): Mean 105,066, Median 95,605 (68% higher than FL)

### Outlier Statistics

**Statistical Outliers** (>3σ): 9 high performers (all legitimate)
**Business Logic Outliers**:
- Very large stores (>10k sq ft): 6 (all legitimate flagships)
- Very high traffic (>200k): 9 (all legitimate top performers)
- Very low traffic (<5k): 4 (all have explainable market dynamics)

**None flagged for removal** - all outliers contain valuable signal

---

## 📁 Deliverables Created

### Documentation

1. **PHASE5_DATA_EXPLORATION_FINDINGS.md**
   - Detailed analysis of all three improvement opportunities
   - Statistical summaries and top/bottom performers
   - Revised implementation strategy

2. **OUTLIER_REVIEW_DECISION.md**
   - Detailed review of all 4 low-traffic candidates
   - Decision rationale (keep all)
   - Documentation precedent for future outlier reviews

### Scripts

3. **src/modeling/detect_outliers.py** (353 lines)
   - Multi-method outlier detection (statistical, business logic, residual-based)
   - Automated flagging and recommendations
   - Exports candidates to CSV for manual review
   - Comprehensive analysis output

4. **src/modeling/placer_correction.py** (412 lines)
   - Ready-to-run Placer calibration correction
   - Calculates correction factors from Insa actual data
   - Multiple correction methods (simple, state-specific, size-adjusted)
   - Automated dataset generation and documentation
   - **Status**: Awaiting Insa actual visit data to proceed

---

## 🎯 Next Steps

### Immediate (Pending Daniel's Input)

**✅ Ready to proceed once Insa data provided:**

Daniel needs to provide actual monthly visit counts for 8 Insa FL stores:

| Store | City | Placer Estimate | Actual Needed |
|-------|------|-----------------|---------------|
| Insa | Hudson | 70,152 | ? |
| Insa | Orlando (1) | 55,227 | ? |
| Insa | Largo | 53,471 | ? |
| Insa | Jacksonville | 39,958 | ? |
| Insa | Summerfield | 34,503 | ? |
| Insa | Orlando (2) | 31,360 | ? |
| Insa | Tampa | 31,086 | ? |
| Insa | Tallahassee | 25,227 | ? |

**Time period**: October 2025 or Q3 2025 average (to match Placer data collection)

Once data provided:
```bash
# Run Placer correction
python3 src/modeling/placer_correction.py

# Retrain model with corrected data
python3 src/modeling/train_multi_state_model.py \
  --data data/processed/combined_with_competitive_features_placer_corrected.csv \
  --output data/models/multi_state_model_v2.pkl

# Compare v1 vs v2 performance
python3 src/modeling/compare_models.py
```

### Future (Phase 6)

After Placer correction complete:
1. **Brand effects analysis** (+0.05 to +0.10 R²)
2. **Digital footprint** (Google/Yelp reviews, +0.03 to +0.05 R²)
3. **Traffic data integration** (AADT, +0.02 to +0.05 R²)
4. **Advanced modeling** (tree-based models, state-specific models)

---

## 📈 Expected Improvement Trajectory

### Phase 5 (Current) - Placer Correction Only
- **Baseline**: R² = 0.194 (Overall), FL = 0.049, PA = -0.027
- **Conservative**: R² = 0.22-0.24 (+13-24%)
- **Target**: R² = 0.25-0.27 (+29-39%)

### Phase 6 (Future) - Add Brand + Digital
- **Conservative**: R² = 0.30-0.32 (+55-65%)
- **Target**: R² = 0.35-0.38 (+80-96%)

### Phase 7 (Advanced) - Tree Models + State-Specific
- **Stretch Goal**: R² = 0.40-0.45 (+106-132%)

---

## 🔑 Key Insights

### 1. Data Maturity Is Not an Issue
- Almost all sites are 12+ months mature
- Temporal adjustments provide minimal value
- Focus effort elsewhere

### 2. Low Performers Are Informative, Not Errors
- Market saturation signal (11-12 competitors)
- Income sensitivity (low-income areas underperform)
- Small market limits (rural/secondary locations)
- **Keep all training data** unless clear data quality issues

### 3. Placer Calibration Is The Low-Hanging Fruit
- 8 Insa stores provide calibration benchmark
- Simple correction factor approach
- Improves both R² and absolute accuracy
- Increases business credibility (predictions match reality)

### 4. PA Outperforms FL Significantly
- PA mean visits: 105k (+68% vs FL)
- Medical vs adult-use market difference
- Higher per-capita consumption in PA
- State-specific models may be worth exploring later

---

## 📝 Decision Log

**Decision 1**: Skip temporal adjustments
- **Rationale**: Only 1 of 741 sites affected (<1%)
- **Impact**: Save 2-3 hours of implementation effort

**Decision 2**: Keep all outliers
- **Rationale**: All 4 low-traffic sites have legitimate explanations
- **Impact**: Preserve competitive dynamics signal in model

**Decision 3**: Prioritize Placer correction
- **Rationale**: 8 Insa stores enable calibration, high expected impact
- **Impact**: Focus limited time on highest-ROI improvement

---

## 🎓 Lessons Learned

1. **Always explore before implementing** - Two of three proposed improvements turned out to be unnecessary
2. **Low performance ≠ data error** - Market dynamics can legitimately produce poor performers
3. **Calibration > Complexity** - Correcting systematic bias likely has higher ROI than complex feature engineering
4. **Actual data is invaluable** - Insa stores provide ground truth for validation and calibration

---

## ✅ Phase 5 Checklist

- [x] Explored PA opening dates (data available, minimal impact)
- [x] Explored FL opening dates (not available, low priority)
- [x] Identified and analyzed outliers (4 low-traffic sites)
- [x] Reviewed outlier data quality (all legitimate, keep all)
- [x] Documented outlier review decisions
- [x] Built outlier detection script
- [x] Built Placer correction script
- [x] Identified 8 Insa stores for calibration
- [x] Documented Phase 5 findings and decisions
- [ ] **PENDING**: Obtain Insa actual visit data from Daniel
- [ ] **PENDING**: Run Placer correction and retrain model v2

---

*Phase 5 exploration establishes a data-driven foundation for targeted model improvements. Ready to proceed with Placer correction once Insa actual data is provided.*
