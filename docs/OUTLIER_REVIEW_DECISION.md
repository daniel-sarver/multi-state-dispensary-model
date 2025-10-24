# Outlier Review Decision

**Date**: October 24, 2025
**Reviewer**: Claude Code
**Status**: Complete - Decision Documented

---

## Summary

**4 low-traffic outliers identified** (<5k visits/month, all FL)
**Decision**: **KEEP ALL 4** - Legitimate stores with explainable low performance
**Recommendation**: Focus on Placer calibration correction instead of outlier removal

---

## Detailed Review

### Site 1: Ayr Cannabis Dispensary - Tallahassee, FL
- **Visits**: 4,201/month
- **Sq Ft**: 3,077
- **Coordinates**: (30.444389, -84.292221) ✅ Valid FL location
- **Match Score**: 91.60 ✅ High confidence
- **Population 5mi**: 171,615 ✅ Good catchment
- **Competitors 5mi**: 12 ⚠️ **Highly saturated**
- **Median HH Income**: $25,735 ⚠️ **Low-income area**

**Analysis**: High competition (12 competitors) in low-income market explains poor performance. Legitimate struggling store.

**Decision**: **KEEP** - Market dynamics explain low visits

---

### Site 2: Trulieve - Tampa, FL
- **Visits**: 2,834/month
- **Sq Ft**: 1,761
- **Coordinates**: (27.995319, -82.519058) ✅ Valid FL location
- **Match Score**: 91.00 ✅ High confidence
- **Population 5mi**: 288,638 ✅ Strong catchment
- **Competitors 5mi**: 11 ⚠️ **Highly saturated**
- **Median HH Income**: $34,167 ⚠️ **Low-income area**

**Analysis**: High competition (11 competitors) in moderate-income market. Large catchment suggests this location may be in a less desirable area (wrong side of Tampa). Trulieve is a major brand, so low performance is noteworthy but not a data error.

**Decision**: **KEEP** - Market saturation explains low visits

---

### Site 3: Mint Cannabis - Cape Coral, FL
- **Visits**: 2,545/month
- **Sq Ft**: 1,014
- **Coordinates**: (26.598488, -81.941910) ✅ Valid FL location
- **Match Score**: 82.00 ⚠️ **Lower confidence**
- **Population 5mi**: 187,607 ✅ Good catchment
- **Competitors 5mi**: 11 ⚠️ **Highly saturated**
- **Median HH Income**: $75,154 ✅ Affluent market

**Analysis**: Lowest match confidence (82) raises slight concern, but coordinates are valid. High competition (11 competitors) in affluent area. Small store (1,014 sq ft) may be in secondary location.

**Decision**: **KEEP (with note)** - Market saturation likely explains low visits. If future analysis shows persistent underprediction, revisit match quality.

---

### Site 4: Curaleaf - St. Augustine, FL
- **Visits**: 1,882/month (LOWEST)
- **Sq Ft**: 956
- **Coordinates**: (29.879131, -81.326019) ✅ Valid FL location
- **Match Score**: 92.80 ✅ High confidence
- **Population 5mi**: 65,835 ⚠️ **Smaller catchment**
- **Competitors 5mi**: 3 ✅ Low competition
- **Median HH Income**: $58,814 ✅ Mid-affluent market

**Analysis**: Smallest catchment (66k) and lowest visits overall. Only 3 competitors suggests this may be a secondary market (St. Augustine is a tourist town, smaller permanent population). Curaleaf is a major brand. Low visits likely due to small market size, not data error.

**Decision**: **KEEP** - Small market size explains low visits

---

## Overall Assessment

**No data quality issues identified**. All 4 sites:
- Have valid FL coordinates ✅
- Have reasonable match scores (82-93) ✅
- Have explainable low performance ✅
  - 3 sites: High competition (11-12 competitors)
  - 1 site: Small market size (66k catchment)

**These are legitimate underperforming stores**, not data errors. They contain valuable signal:
1. **Market saturation effect**: High competition suppresses visits
2. **Income sensitivity**: Low-income areas underperform
3. **Market size limits**: Small catchments have lower ceilings

**Removing these would reduce model's ability to learn competitive dynamics.**

---

## Revised Strategy: Focus on Placer Correction

Given that outlier removal will not help (all outliers are legitimate), **shift focus to Placer visit correction** using Insa data.

### Why Placer Correction is Higher Priority

If Placer systematically underestimates or overestimates visits, the model is learning from biased data. Correcting this bias will:
1. **Improve absolute prediction accuracy** (closer to real visits)
2. **Improve R²** if bias varies by store characteristics
3. **Improve business credibility** (predictions match reality)

### Next Steps

1. ✅ **Outlier review complete** - Keep all training data
2. **Pending**: Obtain Insa actual monthly visits for 8 FL stores
3. Calculate Placer-to-actual correction factor
4. Test correction approaches:
   - Simple average factor
   - Size-adjusted (visits/sq_ft scaling)
   - Market-density adjusted
5. Retrain model with corrected data
6. Measure R² improvement

---

## Expected Impact

### Outlier Removal (Original Plan)
- **Impact if removed**: Likely **negative** (-0.01 to -0.03 R²)
- **Reason**: Losing valuable competitive dynamics signal
- **Decision**: ❌ **Do not remove**

### Placer Correction (New Priority)
- **Expected impact**: +0.03 to +0.08 R²
- **Reason**: Correct systematic bias in training target
- **Decision**: ✅ **Proceed with this approach**

---

## Documentation for Future Reference

This decision establishes the precedent that **low-performing stores should be retained** unless:
1. Coordinates are clearly wrong (outside state boundaries)
2. Match confidence is very low (<75)
3. Store characteristics are impossibleto verify (e.g., 50,000 sq ft)

**Low visits alone is not grounds for removal** - market dynamics can legitimately produce poor performers.

---

*Decision rationale documented for future model improvement efforts.*
