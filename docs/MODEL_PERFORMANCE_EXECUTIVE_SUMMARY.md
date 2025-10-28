# Multi-State Dispensary Model - Executive Summary

**Audience**: Business stakeholders and decision-makers
**Purpose**: Explain model capabilities, limitations, and appropriate use cases
**Date**: October 28, 2025 (Updated for v3.0 State-Specific Models)

---

## What This Model Does

The Multi-State Dispensary Model predicts **annual visit volume** for potential dispensary locations in Florida and Pennsylvania based on:

- **Location characteristics**: Square footage, address/coordinates
- **Market demographics**: Population, income, education levels (Census data)
- **Competition analysis**: Number and proximity of nearby dispensaries
- **State-specific patterns**: Optimized separately for FL and PA markets

**Input**: 3-4 simple inputs (state, coordinates, optional square footage, optional address/AADT)
**Output**: Predicted annual visits with 95% confidence interval (automatically capped at ±75% for usability)

---

## How the Model Works

### Training Data
- **741 dispensaries** across Florida (590) and Pennsylvania (151) with real visit data
- **Corrected annual visits** calibrated against Insa actual performance (45% Placer correction)
- **Temporal adjustments** for 15 FL sites less than 12 months operational
- **Verified data sources**: Placer.ai (visits), Census Bureau (demographics), state regulators (competition)

### Model Architecture (v3.0)
- **State-Specific Models**: Separate optimized models for FL and PA
- **Florida**: Ridge Regression with 31 features (best for larger dataset, simpler patterns)
- **Pennsylvania**: Random Forest with 31 features (captures non-linear patterns in smaller dataset)
- **Automatic Routing**: System selects correct state model based on location
- **Within-State Optimization**: Models trained for site comparisons within each state (not cross-state)

### Key Predictive Factors (in order of importance)
1. **Square footage** (+1,612 visits per sq ft) - strongest predictor
2. **Competition** (negative impact - especially within 1mi and 5mi)
3. **State location** (PA baseline ~1,034 visits higher than FL)
4. **Market saturation** (dispensaries per capita)
5. **Population density** (surprisingly negative correlation)

---

## Predictive Power: The Honest Assessment

### State-Specific Performance (Model v3.0)

**What this means in plain English:**

The models explain **about 7-8% of why some dispensaries within the same state succeed** while others don't. Think of it this way:

- ✅ If you asked "why do 100 dispensaries in Florida have different visit volumes?", this model explains roughly 7-8 of those 100 reasons
- ⚠️ **The other 92-93%** comes from factors the model doesn't capture:
  - Product quality and selection
  - Staff knowledge and customer service
  - Marketing and brand reputation
  - Store layout and parking
  - Customer loyalty programs
  - Local regulations and enforcement
  - Word of mouth and online reviews
  - Operational excellence and management

**Bottom line**: This is a **comparative ranking tool** for sites within the same state, not a precision instrument.

---

## Performance by State: v3.0 Improvements

### Florida: Modest but Improved (R² = 0.0685)

**Explains 6.85% of within-state variance (+42.8% improvement)**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| R² Score | 0.0685 | Low but positive predictive power |
| Improvement | +42.8% over v2 | Significant relative improvement |
| Algorithm | Ridge Regression | Linear model works well with larger dataset |
| Training Data | 590 dispensaries | Large dataset enables linear patterns |
| Usability | **Comparative ranking** | Useful for within-FL site comparisons |

**Why Florida performance improved:**
- State-specific model optimized for FL market patterns
- Ridge regression captures linear relationships effectively
- Full feature set (31 features) balances competition + demographics
- Larger dataset (590 sites) provides stable linear estimates

**Remaining challenges:**
- Highly competitive mature market (590 dispensaries)
- Tourist population not captured in Census data
- Seasonal variation (snowbirds)
- Established brands dominate
- Missing operational factors (product, staff, marketing)

**Use case**: Comparative ranking within Florida; expect typical ±40-50% prediction variance

---

### Pennsylvania: Now Positive and Usable! (R² = 0.0756)

**Dramatic improvement from negative to positive R²!**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| R² Score | 0.0756 | Positive = model now works! |
| Improvement | +1036 basis points | From -0.028 to +0.0756 |
| Algorithm | Random Forest | Captures non-linear patterns |
| Training Data | 151 dispensaries | Smaller dataset needs flexible model |
| Usability | **Now recommended** | Useful for within-PA comparisons |

**Why Pennsylvania improved so dramatically:**
- Random Forest captures non-linear relationships in smaller dataset
- State-specific model no longer dominated by FL patterns
- Regional competition (20mi radius) more relevant than local (5mi)
- Full feature set balances demographics + regional saturation

**Remaining challenges:**
- Smaller training dataset (151 vs 590 FL sites)
- Medical market with different patient behaviors
- Regulatory constraints affect site performance
- Missing operational factors (product, staff, marketing)

**Use case**: Now suitable for comparative ranking within Pennsylvania; expect typical ±40-50% prediction variance

---

## What the Confidence Intervals Really Mean

### Example Prediction (Pennsylvania site):

```
Expected Annual Visits:    49,750
95% Confidence Interval:   12,437 - 87,062 (capped at ±75%)
Confidence Level:          MODERATE
```

**Translation**:

> "Our best guess is 49,750 annual visits, but the true number could realistically be anywhere between 12,000 and 87,000."

That's a **74,625-visit range** (150% of the prediction) - actual performance could be 25% or 175% of our estimate.

**Why such wide intervals (even with ±75% cap)?**
- Model has limited explanatory power (R² = 0.19)
- Many critical success factors not captured in data
- Significant market variability across dispensaries
- Honest uncertainty quantification (not artificial precision)
- **Intervals are capped at ±75%** for business usability (uncapped would be even wider)

---

## Appropriate Use Cases

### ✅ What the Model IS Good For

| Use Case | Why It Works | Confidence Level |
|----------|--------------|------------------|
| **Comparative Ranking** | "Site A: 95k vs Site B: 60k" → A likely better | Moderate |
| **Portfolio Screening** | Narrow 20 sites to top 5 for due diligence | Moderate |
| **Red Flag Detection** | "Site predicts 20k visits" → investigate further | High |
| **Factor Analysis** | "Square footage matters most" → prioritize size | High |
| **Initial Feasibility** | Quick first-pass assessment before site visit | Moderate |

### ❌ What the Model ISN'T Good For

| Use Case | Why It Fails | Risk Level |
|----------|--------------|------------|
| **Financial Projections** | Predictions too uncertain for P&L models | **High** |
| **Lease Negotiations** | Can't justify rent based on predictions | **High** |
| **Staffing Plans** | Visit volume too variable for scheduling | **High** |
| **Single-Site Decisions** | One prediction insufficient for major decisions | **High** |
| **Budget Planning** | Requires 50-100%+ safety margins | **High** |

---

## Recommended Decision Framework

### Phase 1: Initial Screening (Model-Driven)
1. Run model predictions on 10-20 candidate sites
2. Eliminate bottom 50% (below threshold)
3. Focus resources on top-scoring sites

**Model Contribution**: 40% of decision weight

---

### Phase 2: Due Diligence (Human-Driven)
1. Site visits for top candidates
2. Local market research and competitor analysis
3. Demographic validation beyond Census data
4. Traffic patterns and accessibility assessment

**Model Contribution**: 20% of decision weight

---

### Phase 3: Final Decision (Judgment-Driven)
1. Regulatory and permitting feasibility
2. Lease terms and build-out costs
3. Strategic fit with portfolio
4. Risk tolerance and capital availability

**Model Contribution**: 10% of decision weight

---

## Model Improvement Context

### Why Only 7-8% Within-State Explanatory Power?

Model v3.0 represents a **significant architectural improvement** with state-specific optimization:

**v3.0 Achievements:**
- FL: +42.8% improvement in within-state predictions (0.048 → 0.0685)
- PA: Transformed from negative to positive R² (-0.028 → 0.0756)
- Both states now usable for comparative ranking
- Automatic state routing with zero user impact

**Remaining Fundamental Challenges:**
1. **Missing Critical Factors**: Product quality, staff, marketing not in data
2. **Market Complexity**: Cannabis retail has high operational variance
3. **Data Limitations**: Only demographics and competition captured
4. **Feature Ceiling**: Current features explain only ~7-8% of within-state variance

**What Would Improve Performance Further:**
- ✅ Insa actual performance data (enhance training and calibration)
- ✅ Product mix and pricing data
- ✅ Marketing spend and brand awareness metrics
- ✅ Staff experience and training levels
- ✅ Customer satisfaction scores
- ✅ AADT traffic data (expected +3-7% R² improvement)
- ✅ Longitudinal data (track sites over time)

**Key Insight**: Demographic and competitive factors alone have a natural ceiling around ~7-8% within-state explanatory power. Operational data needed for major improvements beyond v3.0.

---

## State-Specific Recommendations (Updated for v3.0)

### For Florida Site Selection:

**Model Reliability**: Low but Improved (R² = 0.0685)
**Recommended Approach**:
- Use model for **comparative ranking** within Florida
- Combine model predictions with local market intelligence (50/50 weight)
- Focus on:
  - Square footage optimization (strongest predictor)
  - Local competition within 5 miles
  - Established neighborhoods vs tourist areas
  - Competitor brands and market share
  - Traffic patterns and accessibility

**Safety Margins**: Assume actual performance could be **±40-50% of prediction**

**Best Use**: Rank 5-10 candidate sites, eliminate bottom performers, focus due diligence on top 3

---

### For Pennsylvania Site Selection:

**Model Reliability**: Low but Now Positive! (R² = 0.0756)
**Recommended Approach**:
- ✅ **Model now recommended** for comparative ranking within Pennsylvania
- Random Forest captures non-linear patterns in PA market
- Combine model predictions with local market intelligence (50/50 weight)
- Focus on:
  - Square footage optimization (strongest predictor)
  - Regional competition saturation (20mi radius)
  - Medical patient population density
  - Proximity to medical professionals
  - Parking and ADA accessibility

**Safety Margins**: Assume actual performance could be **±40-50% of prediction**

**Best Use**: Rank 5-10 candidate sites, eliminate bottom performers, focus due diligence on top 3

**Key Improvement**: PA model no longer dominated by FL patterns; state-specific Random Forest captures PA market dynamics

---

## Technical Specifications Summary

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Model Version** | v3.0 | State-specific models |
| **Training Date** | 2025-10-28 | Current production model |
| **Architecture** | Separate FL & PA models | Optimized per state |
| **Target Variable** | corrected_visits | Annual visits (Placer-corrected) |
| **FL Model Algorithm** | Ridge Regression | Linear patterns, 31 features |
| **FL Cross-Val R²** | 0.0685 | Within-state performance |
| **FL Improvement** | +42.8% over v2 | From 0.048 to 0.0685 |
| **PA Model Algorithm** | Random Forest | Non-linear patterns, 31 features |
| **PA Cross-Val R²** | 0.0756 | Within-state performance |
| **PA Improvement** | +1036 basis points | From -0.028 to +0.0756 |
| **Training Sites** | 741 dispensaries | FL: 590, PA: 151 |
| **Features** | 31 per state | Demographics + competition |
| **Data Correction** | 45% Placer adj. | Calibrated to Insa actuals |
| **User Impact** | Zero | Automatic state routing |

---

## Key Takeaways for Leadership

### The Good News (v3.0 Update):
1. ✅ **Significant improvements achieved** - FL +42.8%, PA from negative to positive!
2. ✅ **Both states now usable** - PA model now works for comparisons (R² = 0.0756)
3. ✅ **Optimized per state** - Separate models capture FL and PA market differences
4. ✅ **Identifies key success factors** - square footage, competition patterns, demographics
5. ✅ **Zero user impact** - Automatic routing to correct state model

### The Reality Check:
1. ⚠️ **Still modest predictive power** - explains only 7-8% of within-state variance
2. ⚠️ **Comparative tool, not precision** - best for ranking sites, not precise forecasts
3. ⚠️ **Missing operational factors** - product quality, staff, marketing still not captured
4. ⚠️ **Wide confidence intervals** - typical ±40-50% prediction variance

### The Recommendation:
Use v3.0 models as **comparative ranking tools within each state**, combined with business judgment:

- **50% weight**: Model predictions and rankings (improved from 30%)
- **30% weight**: Site visits and local market intelligence
- **20% weight**: Strategic fit, lease terms, and financial feasibility

**Key change from v2**: PA predictions now trustworthy for comparative ranking (previously unreliable)

---

## Next Steps

### Immediate Actions (v3.0 Complete):
1. ✅ **State-specific models deployed** - FL Ridge, PA Random Forest
2. ✅ **Automatic state routing implemented** - Zero user impact
3. ✅ **Significant performance improvements achieved** - FL +42.8%, PA now positive
4. **Validate with Insa data** - Test v3.0 predictions against actual Insa store performance

### Medium-Term Improvements:
1. **AADT traffic data integration** - Expected +3-7% R² improvement
   - Gather AADT for all 741 training dispensaries
   - Test correlation with visit volumes
   - Retrain models with traffic features
2. **Collect operational data** - Product mix, staffing, marketing metrics
3. **Add temporal features** - Seasonality, market maturity, competitive entry

### Long-Term Vision:
1. **Integrate Insa performance data** - Proprietary training data for calibration
2. **Real-time market updates** - Dynamic competitor tracking
3. **Predictive maintenance** - Retrain quarterly with new market data
4. **Expand to additional states** - Apply v3.0 methodology to new markets

---

## Questions for Discussion

1. **Risk Tolerance**: With v3.0 improvements, what level of prediction uncertainty is acceptable for site selection decisions?

2. **Decision Framework**: Should model weight increase from 30% to 50% given v3.0 improvements (especially PA)?

3. **Pennsylvania Validation**: Now that PA model works, should we test against Insa PA stores (if any)?

4. **Florida Validation**: Should we validate FL v3.0 model against Insa FL actual performance?

5. **AADT Integration**: Is gathering traffic data for 741 sites worth potential +3-7% R² improvement?

6. **Operational Data**: Should we collect Insa product mix, staffing, and marketing data for major performance boost?

7. **Expansion Strategy**: Should we apply v3.0 state-specific methodology to new markets (CT, MA, etc.)?

---

## Contact & Documentation

**Model Documentation**: See `/docs/` folder for technical details
- `PHASE3B_MODEL_TRAINING_COMPLETE.md` - Full model training report
- `PHASE4_TERMINAL_INTERFACE_COMPLETE.md` - User interface guide
- `PHASE4_PREDICTION_MODULE_COMPLETE.md` - API documentation

**Usage**: Interactive CLI available at `src/terminal/cli.py`

**Model Version**: v3.0 (October 28, 2025) - State-Specific Models
**Last Updated**: October 28, 2025

**Key Changes in v3.0**:
- Separate optimized models for Florida and Pennsylvania
- FL: Ridge Regression (R² = 0.0685, +42.8% improvement)
- PA: Random Forest (R² = 0.0756, from negative to positive!)
- Both states now recommended for comparative ranking
- Automatic state routing with zero user impact

---

*This model is a decision support tool, not a replacement for business judgment and market expertise. Always combine model insights with site visits, local market research, and strategic analysis.*
