# Phase 5: Model Improvement - Data Exploration Findings

**Date**: October 24, 2025
**Purpose**: Document findings from data exploration to inform improvement strategy
**Status**: Complete - Ready for implementation

---

## 🔍 Key Findings Summary

### **Finding 1: Temporal Adjustments Have Limited Applicability**

**Initial Hypothesis**: Many PA dispensaries opened <12 months ago, requiring visit annualization

**Reality**:
- **PA**: Only 1 of 151 training dispensaries opened <12 months ago (0.7%)
  - RISE - York: 7.8 months operational, 99,821 visits
  - All other PA sites are 12+ months mature
- **FL**: No opening dates available in current dataset (0 of 590)
  - Would require historical OMMU report analysis
  - Low priority given limited impact in PA

**Recommendation**: **SKIP temporal adjustments for now**
- Minimal impact on model (affects <1% of training data)
- Focus effort on higher-impact improvements
- Revisit if we acquire FL opening dates in the future

---

### **Finding 2: Outliers Present - Both Statistical and Business Logic**

**Statistical Outliers** (±3 standard deviations):
- **9 high performers** (>200k visits/month)
  - All are legitimate high-traffic stores (not data errors)
  - Examples: Ascend Scranton PA (394k), Organic Remedies Enola PA (271k)
  - Should be **retained** (they contain valuable signal)

**Business Logic Outliers**:
- **6 very large stores** (>10,000 sq ft)
  - Example: Ascend Scranton PA (11,592 sq ft)
  - Legitimate flagship stores

- **4 very low performers** (<5k visits/month)
  - All in Florida
  - Examples: Curaleaf (1,882 visits), Mint Cannabis (2,545 visits)
  - **Possible data quality issues or special circumstances**

**State Differences**:
- **PA**: Higher average (105k visits) vs FL (62k visits)
- **PA**: More variance (std = 57k vs FL 34k)
- **PA**: Higher visit density (likely medical vs FL adult-use)

**Recommendation**: **Conservative outlier removal approach**
1. Identify sites with <5k visits (4 FL sites)
2. Manual review for data quality issues
3. Remove only if confirmed errors (not legitimate low performers)
4. Expected impact: +0.02 to +0.05 R² (modest but worthwhile)

---

### **Finding 3: Insa Stores Available for Placer Calibration**

**Data Availability**:
- **8 Insa FL stores** with Placer data
- Locations: Hudson, Orlando (2), Largo, Jacksonville, Summerfield, Tampa, Tallahassee
- Visit range: 25,227 to 70,152 (average: 42,623)

**Calibration Opportunity**:
If we have actual visit counts for these stores, we can:
1. Calculate Placer-to-actual correction factor
2. Apply systematic correction to all training data
3. Improve absolute prediction accuracy

**Requirements**:
- Actual monthly visit counts for Insa FL stores (from internal data)
- Same time period as Placer data collection (October 2025)
- Can use monthly, quarterly, or annualized data

**Expected Impact**: +0.03 to +0.08 R² (if significant bias exists)

---

## 📊 Detailed Statistics

### Visit Distribution (Training Data, n=741)

**Overall**:
- Mean: 71,066 visits/month
- Median: 62,183 visits/month
- Std Dev: 43,216 visits/month
- Range: 1,882 to 394,345 visits/month

**Florida** (n=590):
- Mean: 62,365 visits/month
- Median: 56,893 visits/month
- Std Dev: 33,932 visits/month
- Range: 1,882 to 260,785 visits/month

**Pennsylvania** (n=151):
- Mean: 105,066 visits/month
- Median: 95,605 visits/month
- Std Dev: 56,843 visits/month
- Range: 16,113 to 394,345 visits/month

### Top 10 Performers (All Visits >196k/month)

| Rank | State | Name | Visits | Sq Ft | Visits/Sq Ft | Competitors 5mi |
|------|-------|------|--------|-------|--------------|-----------------|
| 1 | PA | Ascend Dispensary - Scranton | 394,345 | 11,592 | 34.0 | 3 |
| 2 | PA | Organic Remedies - Enola | 270,651 | 5,074 | 53.3 | 2 |
| 3 | FL | Trulieve | 260,785 | 3,425 | 76.1 | 10 |
| 4 | PA | RISE - Steelton | 221,148 | 6,035 | 36.6 | 1 |
| 5 | PA | Organic Remedies - Chambersburg | 218,609 | 3,310 | 66.1 | 1 |
| 6 | PA | Verilife - Williamsport | 217,337 | 6,894 | 31.5 | 1 |
| 7 | PA | Bloc Dispensary - Edwardsville | 217,266 | 1,862 | 116.7 | 2 |
| 8 | PA | Trulieve - Camp Hill | 216,882 | 5,179 | 41.9 | 3 |
| 9 | PA | Organic Remedies - North Pittsburgh | 213,653 | 5,941 | 36.0 | 0 |
| 10 | PA | Trulieve - Pittsburgh Squirrel Hill | 196,173 | 7,403 | 26.5 | 3 |

**Key Observations**:
- 9 of top 10 are PA (medical market = higher volumes)
- High visits/sq_ft performers (Bloc: 116.7, Trulieve FL: 76.1)
- Low competition sites performing well (North Pittsburgh: 0 competitors in 5mi)

### Bottom 10 Performers (All Visits <15k/month)

| Rank | State | Name | Visits | Sq Ft | Visits/Sq Ft | Competitors 5mi |
|------|-------|------|--------|-------|--------------|-----------------|
| 1 | FL | Curaleaf | 1,882 | 956 | 2.0 | 3 |
| 2 | FL | Mint Cannabis | 2,545 | 1,014 | 2.5 | 11 |
| 3 | FL | Trulieve | 2,834 | 1,761 | 1.6 | 11 |
| 4 | FL | Ayr Cannabis Dispensary | 4,201 | 3,077 | 1.4 | 12 |
| 5 | FL | Trulieve | 6,159 | 1,550 | 4.0 | 11 |
| 6 | FL | Planet 13 | 8,133 | 1,737 | 4.7 | 9 |
| 7 | FL | MUV | 11,131 | 988 | 11.3 | 2 |
| 8 | FL | Green Dragon | 13,017 | 3,223 | 4.0 | 5 |
| 9 | FL | Green Dragon | 13,069 | 2,236 | 5.8 | 8 |
| 10 | FL | Sunnyside* | 14,789 | 3,582 | 4.1 | 8 |

**Key Observations**:
- All bottom performers are in FL
- Very low visits/sq_ft (1.4 to 5.8) suggests possible data quality issues
- High competition may partially explain (8-12 competitors in 5mi)
- **Top 4 (<5k visits) are candidates for outlier removal**

---

## 🎯 Revised Implementation Strategy

### Priority 1: Outlier Analysis & Removal (HIGH IMPACT)
**Effort**: 1-2 hours
**Expected Impact**: +0.02 to +0.05 R²

**Steps**:
1. Manual review of 4 sites with <5k visits
2. Check for data quality issues:
   - Coordinate errors (wrong location?)
   - Square footage errors
   - Store closure/special circumstances
3. Remove confirmed errors (keep legitimate low performers)
4. Retrain model and compare R²

---

### Priority 2: Placer Visit Correction (MEDIUM-HIGH IMPACT)
**Effort**: 2-3 hours (requires Insa actual data)
**Expected Impact**: +0.03 to +0.08 R²

**Steps**:
1. **Daniel to provide**: Actual monthly visit counts for 8 Insa FL stores
2. Calculate Placer/Actual ratio for each store
3. Test correction approaches:
   - Simple average correction factor
   - Store-size-adjusted correction (visits/sq_ft scaling)
   - Market-density-adjusted correction (urban vs suburban)
4. Apply best correction to training data
5. Retrain and validate improvement

**Data Needed from Daniel**:
```
Insa Store           | Location      | Actual Monthly Visits | Time Period
---------------------|---------------|----------------------|-------------
Insa Hudson          | Hudson, FL    | ?                    | Oct 2025 or Q3 2025
Insa Orlando 1       | Orlando, FL   | ?                    | Oct 2025 or Q3 2025
Insa Orlando 2       | Orlando, FL   | ?                    | Oct 2025 or Q3 2025
Insa Largo           | Largo, FL     | ?                    | Oct 2025 or Q3 2025
Insa Jacksonville    | Jacksonville  | ?                    | Oct 2025 or Q3 2025
Insa Summerfield     | Summerfield   | ?                    | Oct 2025 or Q3 2025
Insa Tampa           | Tampa, FL     | ?                    | Oct 2025 or Q3 2025
Insa Tallahassee     | Tallahassee   | ?                    | Oct 2025 or Q3 2025
```

---

### Priority 3: Brand Effects Analysis (FUTURE)
**Effort**: 3-4 hours
**Expected Impact**: +0.05 to +0.10 R²

**Status**: Deferred to Phase 2 (per user request)
- Requires brand name extraction and standardization
- Target encoding implementation
- State-specific brand effects

---

### Priority 4: Digital Footprint (FUTURE)
**Effort**: 2-3 hours
**Expected Impact**: +0.03 to +0.05 R²

**Status**: Deferred to Phase 2 (per user request)
- Google/Yelp review counts and ratings
- Requires API integration

---

## 📝 Next Steps

### Immediate (This Session)
1. **Outlier Analysis Script**: Build tool to identify and analyze outliers
2. **Manual Review**: Review 4 low-performing FL sites for data quality
3. **Baseline Comparison**: Load v1 model and establish comparison metrics
4. **Retrain with Outlier Removal**: Test impact of removing confirmed errors

### Pending Daniel's Input
5. **Insa Actual Data**: Obtain actual visit counts for 8 FL stores
6. **Placer Correction**: Implement and test correction methodology
7. **Final Model Comparison**: v1 vs v2 (outlier removal) vs v3 (+ Placer correction)

### Future Sessions
8. Brand effects analysis and integration
9. Digital footprint data collection and integration
10. Advanced modeling techniques (tree-based models, state-specific models)

---

## 📊 Expected Cumulative Impact

**Conservative Estimate**:
- Outlier removal: +0.02 R²
- Placer correction: +0.03 R²
- **Total**: R² 0.194 → **0.244** (+26% improvement)

**Target Estimate**:
- Outlier removal: +0.05 R²
- Placer correction: +0.08 R²
- **Total**: R² 0.194 → **0.324** (+67% improvement)

**With Future Improvements** (Brand + Digital):
- Additional: +0.08 to +0.15 R²
- **Total**: R² 0.194 → **0.40-0.47** (+106-142% improvement)

---

## 🔑 Key Takeaways

1. **Temporal adjustments not needed**: Only 1 of 741 training sites <12 months old
2. **Outliers exist but are mostly legitimate**: Focus on 4 very low performers
3. **Insa stores enable calibration**: 8 FL stores can inform Placer correction
4. **PA vs FL different markets**: PA medical = 68% higher average visits
5. **Conservative approach recommended**: Remove only confirmed errors, not legitimate extremes

---

*This exploration phase establishes a data-driven foundation for targeted model improvements with realistic expected gains.*
