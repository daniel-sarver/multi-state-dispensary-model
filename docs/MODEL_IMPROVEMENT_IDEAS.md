# Model Improvement Ideas - Priority Queue

**Status**: Planning Phase
**Last Updated**: October 23, 2025
**Target**: Improve overall R² from 0.19 to 0.30+ and PA R² from -0.03 to 0.15+

---

## 🎯 Primary Goal

Improve model predictive power, particularly for Pennsylvania, by incorporating temporal factors, brand effects, and additional accessible data sources.

---

## Priority 1: Temporal Adjustments for Pennsylvania & Florida

### Problem Statement

**Current Issue**: Dispensaries in both states have varying operational histories
- Some sites open < 1 year (ramping up)
- Some sites open 1-3 years (mature)
- Training data treats all sites equally regardless of operational maturity
- Competition counts don't account for when competitors opened

**Impact on Model**:
- Newer sites have artificially low visit counts (not at steady state)
- Competition metrics over-weight recently opened competitors
- Model learns incorrect relationships between features and performance

**Data Availability**:
- **PA**: Opening dates available from state regulator
- **FL**: May need to approximate using historical OMMU reports or old spreadsheet comparisons for sites < 1 year

---

### Solution A: Annualize Visit Counts for New Dispensaries

**Approach**: Project partial-year performance to full-year equivalent

**Implementation**:
```python
# Pseudo-code
if months_open < 12:
    # Apply growth curve adjustment
    maturity_factor = calculate_maturity_factor(months_open)
    annualized_visits = actual_visits / maturity_factor

    # Example maturity curve:
    # 3 months open: 40% of steady state → factor = 0.40
    # 6 months open: 70% of steady state → factor = 0.70
    # 12 months open: 100% of steady state → factor = 1.00
```

**Data Requirements**:
- Opening date for each PA dispensary (already available)
- Define maturity curve (could use Insa's ramp-up data as reference)
- Decide on minimum months open for inclusion (e.g., exclude sites < 3 months)

**Expected Impact**:
- More accurate visit predictions for PA
- Better training signal for model
- Estimated R² improvement: +0.05 to +0.08

---

### Solution B: Time-Weighted Competition Metrics

**Approach**: Weight competitors by fraction of year they were operational

**Implementation**:
```python
# Pseudo-code
for each dispensary:
    for each competitor within radius:
        # Calculate what fraction of the year this competitor existed
        overlap_months = min(12, months_competitor_was_open)
        competitor_weight = overlap_months / 12

        # Apply weight to competition metrics
        weighted_competitor_count += competitor_weight
        weighted_competition_score += (1 / distance) * competitor_weight

# Example:
# Competitor A: Open all year → weight = 1.0
# Competitor B: Opened in July (6 months) → weight = 0.5
# Total weighted competition = 1.0 + 0.5 = 1.5 (instead of 2.0)
```

**Data Requirements**:
- Opening dates for all PA dispensaries (available from state regulator)
- Define reference period (e.g., trailing 12 months from data collection date)

**Expected Impact**:
- More accurate competition intensity measures
- Better model understanding of competitive dynamics
- Estimated R² improvement: +0.03 to +0.05

---

### Combined Temporal Adjustment Strategy

**Phase 1: Data Enhancement**
1. Add `opening_date` column to PA dispensary dataset
2. Calculate `months_operational` as of data collection date
3. Flag dispensaries with < 12 months operation

**Phase 2: Feature Engineering**
1. Create `annualized_visits` feature for training
   - Use actual visits for sites open 12+ months
   - Use projected visits for sites open < 12 months
2. Create time-weighted competition features
   - Replace `competitors_Xmi` with `weighted_competitors_Xmi`
   - Replace `competition_weighted_20mi` with time-adjusted version

**Phase 3: Model Retraining**
1. Retrain with adjusted features
2. Compare performance vs baseline
3. Validate on holdout set

**Timeline**: 1-2 days of work
**Risk**: Low (reversible if doesn't improve performance)

---

## Priority 2: Outlier Detection and Removal

### Problem Statement

**Current Issue**: Outlier data points may be distorting model training
- Extremely high/low performing dispensaries for non-replicable reasons
- Data quality issues (incorrect visit counts, wrong coordinates, etc.)
- Special circumstances (grand opening promotions, temporary closures, etc.)

**Impact on Model**:
- Model tries to fit unusual cases at expense of typical performance
- Coefficients pulled toward extremes
- Reduced predictive power for normal sites

---

### Proposed Approach

**Step 1: Identify Outliers**
```python
# Statistical outlier detection
from scipy import stats

# 1. Residual-based outliers (after initial model fit)
residuals = actual_visits - predicted_visits
z_scores = np.abs(stats.zscore(residuals))
outliers_statistical = dispensaries[z_scores > 3]  # 3 standard deviations

# 2. Leverage-based outliers (unusual feature combinations)
# Use Cook's distance or DFBETAS to identify high-leverage points

# 3. Business logic outliers
outliers_business = dispensaries[
    (dispensaries['sq_ft'] > 10000) |  # Unusually large
    (dispensaries['sq_ft'] < 500) |    # Unusually small
    (dispensaries['monthly_visits'] > 200000) |  # Extremely high traffic
    (dispensaries['monthly_visits'] < 1000)      # Suspiciously low
]
```

**Step 2: Manual Review**
- Review flagged outliers for data quality issues
- Check if extreme values are legitimate (e.g., massive flagship store)
- Document reasons for inclusion/exclusion

**Step 3: Removal Strategy**
```python
# Conservative approach: only remove clear data errors
# Keep legitimate extreme performers (they contain signal)

# Option A: Hard removal
clean_data = data[~data.index.isin(outlier_indices)]

# Option B: Winsorization (cap extremes at percentile)
from scipy.stats.mstats import winsorize
data['monthly_visits_winsorized'] = winsorize(
    data['monthly_visits'],
    limits=[0.01, 0.01]  # Cap bottom/top 1%
)
```

**Expected Impact**:
- Improved coefficient stability
- Better predictions for typical dispensaries
- Estimated R² improvement: +0.02 to +0.05
- Reduced prediction error (lower RMSE)

**Risk**:
- Removing too many points reduces training data
- May remove legitimate high performers with replicable success factors
- Requires careful validation

---

## Priority 3: Placer Visit Correction Using Insa Data

### Problem Statement

**Current Issue**: Placer visit estimates may have systematic bias
- Placer data is modeled from device location pings, not actual counts
- May systematically over/underestimate across different store types
- Bias may vary by state, market density, or store characteristics

**Opportunity**: Use Insa actual performance data to calibrate Placer estimates

---

### Proposed Methodology

**Step 1: Calculate Placer Accuracy Ratio for Insa Stores**
```python
# For each Insa store with both Placer and actual visit data
insa_stores = [
    {'name': 'Insa FL Store 1', 'placer_visits': 45000, 'actual_visits': 52000},
    {'name': 'Insa FL Store 2', 'placer_visits': 38000, 'actual_visits': 41000},
    # ... more stores
]

# Calculate correction factor
placer_to_actual_ratio = actual_visits / placer_visits
mean_correction_factor = np.mean([store['actual_visits'] / store['placer_visits']
                                  for store in insa_stores])

# Example: if Placer underestimates by 15%, correction_factor = 1.15
```

**Step 2: Apply Correction to Model Predictions**
```python
# Option A: Correct training data (preferred)
# Adjust Placer visits before training
corrected_visits = placer_visits * correction_factor
model.fit(features, corrected_visits)

# Option B: Correct predictions (alternative)
# Train on raw Placer data, correct output
raw_prediction = model.predict(features)
corrected_prediction = raw_prediction * correction_factor
```

**Step 3: State/Market-Specific Corrections (Advanced)**
```python
# If Placer accuracy varies by context
correction_factors = {
    'FL_urban': 1.12,      # Placer underestimates urban FL by 12%
    'FL_suburban': 1.08,   # Placer underestimates suburban FL by 8%
    'PA_urban': 1.05,      # Placer underestimates urban PA by 5%
    'PA_suburban': 1.15,   # Placer underestimates suburban PA by 15%
}

# Apply context-specific correction
dispensary['market_type'] = classify_market(population_density, state)
correction = correction_factors[f"{state}_{market_type}"]
corrected_visits = placer_visits * correction
```

**Data Requirements**:
- Insa store actual visit counts (monthly or annualized)
- Corresponding Placer estimates for same stores and time period
- Sufficient sample size (ideally 5+ stores for reliable calibration)

**Expected Impact**:
- More accurate absolute visit predictions
- Better calibration of confidence intervals
- Estimated improvement: +0.03 to +0.08 R² (if significant bias exists)
- Improved business credibility (predictions closer to reality)

**Validation**:
- Cross-validate on holdout Insa stores
- Check if correction improves out-of-sample predictions
- Compare corrected model RMSE vs uncorrected

---

## Priority 4: Brand Effects Analysis

### Problem Statement

**Current Issue**: Model treats all dispensaries as identical brands
- No distinction between Curaleaf, Trulieve, Cresco, etc.
- Brand reputation, loyalty, and marketing not captured
- Premium brands may drive higher traffic independent of location

**Hypothesis**: Brand identity explains 5-15% of visit variance

---

### Proposed Analysis

**Step 1: Brand Identification**
- Extract brand/operator name from regulator data or Placer data
- Standardize naming (e.g., "Curaleaf Holdings" → "Curaleaf")
- Create brand categories:
  - National MSOs (Curaleaf, Trulieve, Cresco, GTI, Verano)
  - Regional players (specific to FL or PA)
  - Independent single-site operators

**Step 2: Exploratory Data Analysis**
```python
# Questions to answer:
1. Do MSO dispensaries have higher average visits than independents?
2. Which brands consistently outperform location-based predictions?
3. Is brand effect consistent across states or state-specific?
4. Does brand matter more in competitive markets?

# Visualization:
- Box plots of visits by brand category
- Residual analysis: which brands have consistent positive residuals?
- Brand × competition interaction effects
```

**Step 3: Feature Engineering Options**

**Option A: Binary Brand Flags**
```python
features = [
    'is_MSO',  # 1 if national MSO, 0 otherwise
    'is_curaleaf',
    'is_trulieve',
    # ... top 5-10 brands
]
```

**Option B: Brand Performance Index**
```python
# Calculate historical average performance by brand
brand_avg_visits = df.groupby('brand')['monthly_visits'].mean()

# Create index (1.0 = average brand performance)
brand_performance_index = brand_avg_visits / df['monthly_visits'].mean()

# Use as feature
features['brand_index'] = dispensary_brand_index
```

**Option C: Brand Market Share**
```python
# Calculate brand's local market share within radius
for radius in [5, 10, 20]:
    features[f'brand_market_share_{radius}mi'] = (
        count_same_brand_within_radius / total_competitors_within_radius
    )
```

---

### Implementation Steps

1. **Data Collection** (2-4 hours)
   - Extract brand names from datasets
   - Standardize and clean brand identifiers
   - Manual review for accuracy

2. **EDA** (2-4 hours)
   - Statistical tests for brand effects
   - Visualization of brand performance
   - Identify top-performing brands

3. **Feature Engineering** (2-3 hours)
   - Implement chosen approach (likely Option B: Performance Index)
   - Add to feature_engineering pipeline

4. **Model Testing** (1-2 hours)
   - Retrain with brand features
   - Compare R² improvement
   - Validate brand coefficients make sense

**Expected Impact**:
- Estimated R² improvement: +0.05 to +0.10 (if brand matters)
- Could be negligible if brand is proxy for location quality
- Worth testing - easy to implement and reverse

**Risk**: Medium
- May not improve predictions if brand effect is location-dependent
- Could introduce multicollinearity if brand correlates with square footage
- Requires careful validation

---

## Priority 3: Additional Accessible Data Sources

### Goal
Identify and integrate new data sources that:
1. Are publicly accessible or affordable
2. Have good geographic coverage (FL & PA)
3. Correlate with dispensary success
4. Don't duplicate existing features

---

### Candidate Data Sources

#### A. Traffic & Accessibility Data (HIGH PRIORITY)

**Source**: State DOT AADT (Annual Average Daily Traffic) data
- **Availability**: Public, free, FL & PA available
- **Coverage**: Major roads and highways
- **Hypothesis**: Higher traffic roads = more visibility and accessibility = more visits

**Implementation**:
```python
features = [
    'nearest_road_aadt',  # Traffic on closest road
    'max_aadt_1mi',       # Highest traffic road within 1 mile
    'weighted_traffic_score'  # Distance-weighted sum of nearby road traffic
]
```

**Expected Impact**: +0.02 to +0.05 R²
**Effort**: Medium (requires spatial joins)
**Status**: Planned in original project scope but not yet implemented

---

#### B. Points of Interest (POI) Density (MEDIUM PRIORITY)

**Source**: OpenStreetMap, Yelp API, Google Places API
- **Availability**: Free (OSM) or affordable (Yelp/Google)
- **Coverage**: Excellent for urban areas

**Features**:
```python
features = [
    'restaurants_1mi',      # Food traffic attracts foot traffic
    'retail_stores_1mi',    # Shopping centers drive visits
    'medical_offices_1mi',  # Relevant for medical dispensaries (PA)
    'parking_lots_500m',    # Parking availability proxy
    'transit_stops_1mi'     # Public transit accessibility
]
```

**Expected Impact**: +0.01 to +0.03 R²
**Effort**: Medium (API calls, data cleaning)

---

#### C. Demographic Mobility Data (MEDIUM PRIORITY)

**Source**: Census Transportation Planning Products (CTPP)
- **Availability**: Free, Census Bureau
- **Coverage**: Census tract level

**Features**:
```python
features = [
    'workers_commuting_through_tract',  # Commuter traffic
    'pct_work_from_home',               # Daytime population
    'median_commute_time',              # Mobility proxy
    'vehicles_per_household'            # Car ownership = accessibility
]
```

**Expected Impact**: +0.01 to +0.02 R²
**Effort**: Low (similar to existing census integration)

---

#### D. Parking & Visibility Proxies (LOW-MEDIUM PRIORITY)

**Source**: Satellite imagery analysis (Google Maps API, Mapbox)
- **Availability**: Free tier available
- **Coverage**: Excellent

**Features** (requires image analysis):
```python
features = [
    'parking_lot_area_sqm',      # Calculated from satellite
    'building_setback_from_road', # Visibility proxy
    'signage_visibility_score',   # Manual scoring or ML
    'street_frontage_meters'      # Road exposure
]
```

**Expected Impact**: +0.02 to +0.04 R² (if visibility matters)
**Effort**: High (requires image processing or manual coding)

---

#### E. Crime & Safety Data (LOW PRIORITY)

**Source**: Local police departments, FBI UCR data
- **Availability**: Varies by jurisdiction
- **Coverage**: City/county level (may not have tract-level)

**Features**:
```python
features = [
    'violent_crime_rate_per_1000',
    'property_crime_rate_per_1000',
    'safety_perception_score'  # Survey data
]
```

**Expected Impact**: +0.01 to +0.02 R² (likely minimal)
**Effort**: High (data availability issues, privacy concerns)
**Risk**: May introduce bias, questionable business value

---

#### F. Zoning & Land Use Data (LOW PRIORITY)

**Source**: County/city zoning maps
- **Availability**: Public but fragmented
- **Coverage**: Good but requires custom processing per jurisdiction

**Features**:
```python
features = [
    'is_commercial_corridor',    # C1/C2 zoning
    'is_mixed_use_zone',
    'residential_density_zone',   # R1 vs R5 zoning
    'walkability_score'           # Derived from zoning
]
```

**Expected Impact**: +0.01 to +0.02 R² (likely redundant with existing features)
**Effort**: High (custom per jurisdiction)

---

### Recommended Priority Order

1. **Traffic Data (AADT)** - Already planned, high expected impact
2. **Brand Effects** - Easy to test, potentially high impact
3. **Temporal Adjustments (PA)** - Critical for PA model viability
4. **POI Density** - Moderate effort, proven in retail literature
5. **Demographic Mobility** - Low effort, marginal benefit

**Skip for now**:
- Parking/visibility (high effort, unclear ROI)
- Crime data (data quality issues, ethical concerns)
- Zoning data (likely redundant)

---

## Implementation Roadmap

### Phase 1: Quick Wins (1-2 days)
1. ✅ Add temporal adjustments for PA dispensaries
   - Annualize visits for sites < 12 months old
   - Time-weight competition metrics
2. ✅ Test brand effects
   - Extract and standardize brand names
   - Calculate brand performance index
   - Add as feature and measure impact

**Expected R² improvement**: +0.05 to +0.15
**Probability of success**: High (70%+)

---

### Phase 2: Data Integration (2-3 days)
1. ✅ Integrate AADT traffic data
   - Download FL & PA DOT data
   - Spatial join to dispensary locations
   - Create traffic accessibility features
2. ✅ Add POI density features
   - Query OpenStreetMap for key POI categories
   - Calculate density within multiple radii
   - Test impact on model

**Expected R² improvement**: +0.03 to +0.08
**Probability of success**: Medium (50-60%)

---

### Phase 3: Model Refinement (1-2 days)
1. ✅ Feature selection and regularization
   - Remove redundant features
   - Test alternative regularization (Lasso, Elastic Net)
   - Optimize hyperparameters
2. ✅ Ensemble methods
   - Test Random Forest, Gradient Boosting
   - Compare to Ridge regression baseline

**Expected R² improvement**: +0.02 to +0.05
**Probability of success**: Medium (40-50%)

---

## Success Metrics

**Current Performance**:
- Overall R² = 0.194
- Florida R² = 0.049
- Pennsylvania R² = -0.027

**Target Performance** (after improvements):
- Overall R² = 0.30+ (55% improvement)
- Florida R² = 0.15+ (3x improvement)
- Pennsylvania R² = 0.15+ (from negative to usable)

**Minimum Viable Improvement**:
- Overall R² = 0.25 (29% improvement)
- Florida R² = 0.10 (2x improvement)
- Pennsylvania R² = 0.05 (from negative to marginally useful)

---

## Data Requirements Checklist

### For Temporal Adjustments
- [ ] Opening dates for all PA dispensaries
- [ ] Opening dates for all PA competitors
- [ ] Define maturity curve (use Insa ramp data if available)
- [ ] Validation: compare projected vs actual for mature sites

### For Brand Analysis
- [ ] Brand/operator names from regulator data
- [ ] Standardized brand mapping (MSO identification)
- [ ] Manual review of brand assignments
- [ ] Decision on brand feature approach (binary, index, or market share)

### For Traffic Data
- [ ] FL DOT AADT dataset (download)
- [ ] PA DOT AADT dataset (download)
- [ ] Road network shapefiles (spatial join)
- [ ] Distance calculation method (nearest road, weighted average)

### For POI Data
- [ ] OpenStreetMap API access (free)
- [ ] POI categories to query (restaurants, retail, medical, parking)
- [ ] Radius definitions (500m, 1mi, 3mi?)
- [ ] Rate limiting strategy for API calls

---

## Risk Assessment

| Initiative | Effort | Expected Gain | Risk | Priority |
|------------|--------|---------------|------|----------|
| PA Temporal Adjustments | Medium | High (+0.08) | Low | **HIGH** |
| Brand Effects | Low | Medium (+0.07) | Medium | **HIGH** |
| Traffic Data (AADT) | Medium | Medium (+0.05) | Low | **MEDIUM** |
| POI Density | Medium | Low (+0.02) | Low | **MEDIUM** |
| Ensemble Methods | Low | Low (+0.03) | Low | **LOW** |

**Recommended Focus**: PA Temporal Adjustments + Brand Effects
- Combined expected improvement: +0.10 to +0.15 R²
- Would bring overall R² from 0.19 → 0.29-0.34 (within target range)
- Would bring PA R² from -0.03 → 0.10-0.15 (usable for business)

---

## Next Steps

1. **Immediate** (next session):
   - Collect PA opening dates from regulator data
   - Extract and standardize brand names
   - Implement temporal adjustment logic
   - Calculate brand performance indices

2. **Short-term** (following session):
   - Retrain model with temporal + brand features
   - Validate improvements on test set
   - Update confidence intervals if RMSE changes
   - Document results

3. **Medium-term** (if Phase 1 succeeds):
   - Integrate traffic data
   - Add POI density features
   - Consider ensemble methods

4. **Long-term** (future improvement cycles):
   - Incorporate Insa actual performance data for calibration
   - Build state-specific models (separate FL and PA)
   - Add temporal forecasting (predict future performance)

---

## Questions for Daniel

1. **PA Opening Dates**: Do we have access to PA dispensary opening dates already, or do we need to scrape state regulator website?

2. **Maturity Curve**: Do we have Insa's historical ramp-up data (first 12 months of performance) to inform the maturity adjustment curve?

3. **Brand Data**: Are brand names already in the Placer dataset, or do we need to match them from another source?

4. **Traffic Data**: Is AADT integration still a priority, or should we focus on temporal/brand first?

5. **Success Criteria**: What minimum R² would make the model "good enough" for your site selection process? (Target 0.30?)

---

## 🔬 Advanced Experiments (Codex Recommendations)

### Additional Data Sources - Codex Suggestions

**High-Value, Low-Effort Options:**

1. **Digital Footprint / Marketing Proxies**
   - Google review count and average rating
   - Yelp rating and review count
   - Social media followers (Instagram, Facebook)
   - **Expected Impact**: +0.03 to +0.05 R² (marketing effectiveness proxy)
   - **Effort**: Low (public APIs available)
   - **Priority**: High (easy win)

2. **Commercial Context**
   - Nearby retail density (POI count within radius)
   - Shopping center size (if in a center)
   - Anchor tenants (Walmart, Target, grocery stores nearby)
   - **Source**: SafeGraph, Foursquare, OpenStreetMap
   - **Expected Impact**: +0.02 to +0.04 R² (foot traffic proxy)
   - **Effort**: Medium (API integration)

3. **Economic Indicators**
   - County/zip-level unemployment rate
   - Median home price (housing affordability)
   - **Source**: Bureau of Labor Statistics, Zillow API
   - **Expected Impact**: +0.01 to +0.02 R² (economic health proxy)
   - **Effort**: Low (readily available)

4. **Tourism / Leisure Proximity**
   - Distance to beaches (FL specific)
   - Distance to casinos
   - Distance to colleges/universities
   - **Rationale**: Captures transient customer base
   - **Expected Impact**: +0.02 to +0.03 R² (especially for FL)
   - **Effort**: Low (simple distance calculations)

5. **Parking Availability**
   - Parking lot size (from satellite imagery)
   - Street parking availability (parking.com API)
   - **Expected Impact**: +0.01 to +0.02 R² (accessibility factor)
   - **Effort**: Medium (requires image processing or API)

### Modeling Techniques to Explore

**1. Tree-Based Models**
- Random Forest, Gradient Boosting (XGBoost, LightGBM)
- Capture non-linear relationships better than Ridge
- Can handle feature interactions automatically
- **Effort**: Low (quick to test with existing features)
- **Expected Impact**: +0.05 to +0.10 R² (if non-linearities matter)

**2. State-Specific Models**
- Train separate models for FL and PA
- Avoids forcing both states into single parameter set
- **Rationale**: FL and PA markets fundamentally different
- **Expected Impact**: +0.03 to +0.08 R² (especially for PA)

**3. Stacking Ensemble**
- Combine Ridge, Random Forest, Gradient Boosting
- Meta-learner learns optimal weighting
- **Expected Impact**: +0.02 to +0.05 R² (often marginal but reliable)
- **Effort**: Medium (requires careful cross-validation)

### Feature Engineering - Advanced

**1. Feature Interactions (Codex-suggested)**
```python
# Business-intuitive interactions
interactions = [
    'sq_ft × saturation_5mi',           # Size matters more in saturated markets
    'brand_index × population_density',  # Brand value in dense markets
    'competitors_5mi × median_income',   # Competition impact varies by affluence
    'pop_5mi × is_shopping_center',     # Foot traffic amplification
]
```

**2. Temporal/Seasonal Features**
- Month-of-year indicators (if monthly data available)
- Seasonality flags (winter vs summer for FL tourism)
- Weather proxies (average temperature, precipitation)

**3. Geospatial Smoothing**
- County-level fixed effects
- Spatially-smoothed visit averages (borrow strength from neighbors)
- **Codex note**: Absorbs regional heterogeneity not captured by features

**4. Data Quality Enhancements**
- Flag outliers (extremely large/small stores)
- Winsorize heavy tails (cap extreme values)
- Consider segmentation (MSO vs independent models)

### Brand Effects - Enhanced (Codex Refinement)

**Target Encoding Approach** (recommended by Codex):
```python
# Instead of simple binary flags, use regularized target encoding
brand_mean_visits = df.groupby('brand')['monthly_visits'].mean()
global_mean = df['monthly_visits'].mean()

# Regularize to avoid overfitting small brands
def regularized_target_encode(brand, count, alpha=10):
    brand_effect = (count * brand_mean + alpha * global_mean) / (count + alpha)
    return brand_effect / global_mean  # Normalize to 1.0 = average

# Use in model as continuous feature
features['brand_performance_index'] = regularized_target_encode(...)
```

**Brand × State Interactions**:
- Certain chains may have different reputation by state
- E.g., Curaleaf strong in FL but weaker in PA
- **Implementation**: `brand_index_FL`, `brand_index_PA` as separate features

---

## 🎯 Revised Priority Roadmap (User-Focused Implementation Order)

### Phase 1: Data Quality & Temporal Improvements (1-2 days)
**Target: +0.10 to +0.15 R²**

1. ✅ **Temporal Adjustments (PA & FL)**
   - Annualize visits for sites < 12 months (both states)
   - Time-weight competition metrics
   - Approximate FL opening dates from historical OMMU reports
   - **Codex endorsement**: "Can remove a lot of noise"
   - **Expected**: +0.05 to +0.08 R²

2. ✅ **Outlier Detection and Removal**
   - Identify statistical outliers (residuals, leverage)
   - Business logic filters (extreme sq_ft, visits)
   - Manual review and data quality validation
   - **Expected**: +0.02 to +0.05 R²

3. ✅ **Placer Visit Correction**
   - Calculate Insa actual-to-Placer ratio
   - Apply correction factor to training data
   - State/market-specific corrections if needed
   - **Expected**: +0.03 to +0.08 R²

**Phase 1 Total Expected Improvement**: +0.10 to +0.21 R² (would achieve 0.29-0.40 overall)

### Phase 2: Brand Effects & Digital Footprint (2-3 days)
**Target: +0.08 to +0.15 R²**

1. ✅ **Brand Effects (with target encoding)**
   - Regularized target encoding (not simple one-hot)
   - Brand × state interactions
   - **Codex endorsement**: "Real, persistent lifts"
   - **Expected**: +0.05 to +0.10 R²

2. ✅ **Digital Footprint Features**
   - Google/Yelp reviews (counts and ratings)
   - Social media followers
   - **Rationale**: Easy to collect, marketing proxy
   - **Codex suggestion**: Low-effort, often helpful
   - **Expected**: +0.03 to +0.05 R²

**Phase 2 Total Expected Improvement**: +0.08 to +0.15 R² (cumulative: 0.37-0.55 overall)

### Phase 3: Advanced Modeling (1-2 days)
**Target: +0.03 to +0.08 R²**

1. ✅ Tree-Based Models
   - Test Random Forest, XGBoost
   - Compare to Ridge baseline
   - **Codex recommendation**: "Capture non-linear effects"

2. ✅ State-Specific Models
   - Separate FL and PA models
   - **Codex rationale**: Markets fundamentally different

3. ✅ Stacking Ensemble
   - Combine multiple model types
   - Meta-learner optimization

### Phase 4: Refinements (ongoing)
**Target: +0.02 to +0.05 R²**

1. ✅ Geospatial Smoothing
   - County fixed effects
   - Spatial averaging

2. ✅ Data Quality Audit
   - Outlier detection and handling
   - Winsorization for extremes

3. ✅ Temporal Features
   - Seasonality if data available

---

## 📊 Updated Success Targets (with Codex suggestions)

### Conservative Estimate
**Phase 1 only** (temporal + brand + digital)
- Overall R²: 0.19 → **0.30** (+58%)
- PA R²: -0.03 → **0.12** (from broken to marginal)

### Target Performance
**Phases 1-2** (+ commercial context + tourism + interactions)
- Overall R²: 0.19 → **0.35** (+84%)
- PA R²: -0.03 → **0.18** (from broken to usable)

### Stretch Goal
**Phases 1-3** (+ tree models + state-specific + ensemble)
- Overall R²: 0.19 → **0.40** (+111%)
- PA R²: -0.03 → **0.25** (from broken to good)

**Codex Assessment**: "Even a simple stacking ensemble might lift R²" - suggests 0.35-0.40 is achievable

---

## 🔑 Key Insights from Codex Review

1. **Opening-date adjustments are high-value**: "Can remove a lot of noise" - prioritize this
2. **Target encoding > one-hot for brands**: Regularized encoding avoids overfitting small brands
3. **Digital footprint is low-hanging fruit**: Review counts/ratings are easy to collect and informative
4. **Tree models likely to help**: Ridge assumes linearity; reality is non-linear
5. **State-specific models worth testing**: FL and PA are different enough to warrant separate treatment
6. **Feature interactions matter**: sq_ft × saturation, brand × density have business logic

---

*This document serves as the comprehensive roadmap for model improvement efforts. Prioritize Phase 1 (temporal + brand + digital) for maximum impact with minimum effort, then proceed to Phases 2-3 based on results.*
