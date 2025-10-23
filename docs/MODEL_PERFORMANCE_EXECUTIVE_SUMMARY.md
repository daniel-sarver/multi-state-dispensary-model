# Multi-State Dispensary Model - Executive Summary

**Audience**: Business stakeholders and decision-makers
**Purpose**: Explain model capabilities, limitations, and appropriate use cases
**Date**: October 23, 2025

---

## What This Model Does

The Multi-State Dispensary Model predicts monthly visit volume for potential dispensary locations in Florida and Pennsylvania based on:

- **Location characteristics**: Square footage, address/coordinates
- **Market demographics**: Population, income, education levels (Census data)
- **Competition analysis**: Number and proximity of nearby dispensaries
- **State-specific factors**: Florida vs Pennsylvania market differences

**Input**: 23 site characteristics (square footage, population radii, competitor counts, demographics)
**Output**: Predicted monthly visits with 95% confidence interval

---

## How the Model Works

### Training Data
- **741 dispensaries** across Florida and Pennsylvania with real visit data
- **937 total sites** including competitive landscape
- **Verified data sources**: Placer.ai (visits), Census Bureau (demographics), state regulators (competition)

### Model Type
- **Ridge Regression** with state interaction terms
- Analyzes 44 features total (23 user-provided + 21 auto-generated)
- Trained on 2+ years of market data

### Key Predictive Factors (in order of importance)
1. **Square footage** (+2,945 visits per 1,000 sq ft) - strongest predictor
2. **Competition** (negative impact - more competitors = fewer visits)
3. **Population within 5 miles** (positive but moderate impact)
4. **State location** (PA baseline higher than FL)
5. **Demographics** (income, education, population density)

---

## Predictive Power: The Honest Assessment

### Overall Performance: **R² = 0.19 (19%)**

**What this means in plain English:**

The model explains **about 19% of why some dispensaries succeed** while others don't. Think of it this way:

- ✅ If you asked "why do 100 dispensaries have different visit volumes?", this model explains roughly 19 of those 100 reasons
- ⚠️ **The other 81%** comes from factors the model doesn't capture:
  - Product quality and selection
  - Staff knowledge and customer service
  - Marketing and brand reputation
  - Store layout and parking
  - Customer loyalty programs
  - Local regulations and enforcement
  - Word of mouth and online reviews

**Bottom line**: This is a **screening and comparison tool**, not a crystal ball.

---

## Performance by State: Critical Differences

### Florida: Weak (R² = 0.05)

**Explains only 5% of success variance**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| R² Score | 0.05 | Very weak predictive power |
| Prediction Uncertainty | ±33,000 visits | Lower uncertainty, low accuracy |
| Usability | **Rough ballpark only** | Directional guidance at best |

**Why Florida is hard to predict:**
- Highly competitive mature market
- Tourist population not captured in Census data
- Seasonal variation (snowbirds)
- Established brands dominate

**Use case**: Rough estimates for comparative ranking only

---

### Pennsylvania: Very Weak (R² = -0.03)

**Worse than guessing the average!**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| R² Score | -0.03 | Essentially doesn't work |
| Prediction Uncertainty | ±57,000 visits | Very high uncertainty |
| Usability | **Not recommended** | Use PA market averages instead |

**Why Pennsylvania doesn't work:**
- Smaller training dataset (fewer PA dispensaries)
- Different market dynamics than Florida
- Medical-only market structure (at training time)
- Regulatory differences affect operations

**Use case**: Model predictions should be heavily discounted; rely on local market knowledge

---

## What the Confidence Intervals Really Mean

### Example Prediction (Florida site):

```
Expected Monthly Visits:   79,893
95% Confidence Interval:   14,897 - 144,889
Confidence Level:          LOW
```

**Translation**:

> "Our best guess is 80,000 visits/month, but the true number is almost certainly somewhere between 15,000 and 145,000."

That's a **130,000-visit range** - the actual performance could be **10x our prediction** (either higher or lower).

**Why such wide intervals?**
- Model has limited explanatory power (R² = 0.19)
- Many critical success factors not captured in data
- Significant market variability across dispensaries
- Honest uncertainty quantification (not artificial precision)

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

### Why Only 19% Explanatory Power?

This model represents a **2.6x improvement** over the baseline single-state model (R² = 0.07 → 0.19), but still faces fundamental limitations:

**Fundamental Challenges:**
1. **Missing Critical Factors**: Product quality, staff, marketing not in data
2. **Market Complexity**: Cannabis retail has high operational variance
3. **Data Limitations**: No proprietary Insa performance data in training
4. **State Differences**: FL and PA markets operate very differently

**What Would Improve Performance:**
- ✅ Insa actual performance data (validate and calibrate predictions)
- ✅ Product mix and pricing data
- ✅ Marketing spend and brand awareness metrics
- ✅ Staff experience and training levels
- ✅ Customer satisfaction scores
- ✅ Longitudinal data (track sites over time)

Without access to operational data, **demographic and competitive factors alone explain only ~20%** of dispensary success.

---

## State-Specific Recommendations

### For Florida Site Selection:

**Model Reliability**: Very Low
**Recommended Approach**:
- Use model for initial screening only (eliminate bottom quartile)
- **Weight local market intelligence heavily** (60%+ of decision)
- Focus on:
  - Established neighborhoods vs tourist areas
  - Competitor brands and market share
  - Traffic patterns and accessibility
  - Lease economics and build-out costs

**Safety Margins**: Assume actual performance could be **±50% of prediction**

---

### For Pennsylvania Site Selection:

**Model Reliability**: Extremely Low
**Recommended Approach**:
- **Discount model predictions significantly**
- Use PA market averages as baseline instead
- Focus on:
  - Medical patient population density
  - Proximity to medical professionals
  - Parking and ADA accessibility
  - Regulatory compliance ease

**Safety Margins**: Assume actual performance could be **±75% of prediction**

**Alternative**: Consider building PA-specific model with more PA-only training data

---

## Technical Specifications Summary

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Overall R²** | 0.194 | Explains 19% of variance |
| **Cross-Validation R²** | 0.187 ± 0.065 | Consistent across data splits |
| **Test RMSE** | 39,024 visits | Average prediction error |
| **Florida R²** | 0.049 | Very weak (5% variance) |
| **Florida RMSE** | 33,162 visits | Lower error, still weak |
| **Pennsylvania R²** | -0.027 | Negative (worse than mean) |
| **Pennsylvania RMSE** | 56,581 visits | High error, unreliable |
| **Training Sites** | 741 dispensaries | Large dataset |
| **Features** | 44 total | Comprehensive coverage |
| **Improvement** | 2.62x over baseline | Significant progress |

---

## Key Takeaways for Leadership

### The Good News:
1. ✅ **Best available model** for multi-state screening (2.6x better than baseline)
2. ✅ **Identifies key success factors** (square footage, population, competition)
3. ✅ **Efficient screening tool** for large site portfolios
4. ✅ **Honest uncertainty** quantification (wide confidence intervals reflect reality)

### The Reality Check:
1. ⚠️ **Not a precision instrument** - explains only 19% of success factors
2. ⚠️ **Florida predictions weak** - R² = 0.05 means very rough estimates
3. ⚠️ **Pennsylvania predictions unreliable** - negative R² means don't trust numbers
4. ⚠️ **Wide confidence intervals** - typical ±50-100k visit range

### The Recommendation:
Use this model as **one input in a multi-factor decision process**, not as the primary decision-maker:

- **30% weight**: Model predictions and rankings
- **40% weight**: Site visits and local market intelligence
- **30% weight**: Strategic fit, lease terms, and financial feasibility

**Never make a major site decision based on model predictions alone.**

---

## Next Steps

### Immediate Actions:
1. **Validate with Insa data** - Test predictions against actual Insa store performance
2. **Calibrate confidence intervals** - Check if 95% CI coverage is accurate
3. **Refine use cases** - Define specific scenarios where model adds value

### Medium-Term Improvements:
1. **Collect operational data** - Product mix, staffing, marketing metrics
2. **Build state-specific models** - Separate FL and PA models with more data
3. **Add temporal features** - Seasonality, market maturity, competitive entry

### Long-Term Vision:
1. **Integrate Insa performance data** - Proprietary training data for calibration
2. **Real-time market updates** - Dynamic competitor tracking
3. **Predictive maintenance** - Retrain quarterly with new market data

---

## Questions for Discussion

1. **Risk Tolerance**: What level of prediction uncertainty is acceptable for site selection decisions?

2. **Decision Framework**: How should model predictions be weighted against site visits and local knowledge?

3. **Pennsylvania Strategy**: Given weak PA predictions, should we use alternative screening methods for PA sites?

4. **Validation Priority**: Should we validate model against Insa actual performance before broader deployment?

5. **Improvement Investment**: Is enhancing model performance (collecting operational data) worth the effort given current limitations?

---

## Contact & Documentation

**Model Documentation**: See `/docs/` folder for technical details
- `PHASE3B_MODEL_TRAINING_COMPLETE.md` - Full model training report
- `PHASE4_TERMINAL_INTERFACE_COMPLETE.md` - User interface guide
- `PHASE4_PREDICTION_MODULE_COMPLETE.md` - API documentation

**Usage**: Interactive CLI available at `src/terminal/cli.py`

**Model Version**: v1.0 (October 23, 2025)
**Last Updated**: October 23, 2025

---

*This model is a decision support tool, not a replacement for business judgment and market expertise. Always combine model insights with site visits, local market research, and strategic analysis.*
