# Post-Phase 6 Continuation - Model v2 Usage & Analysis

## Quick Start Continuation Prompt

Copy/paste this after compacting:

> **"Phase 6 complete. Model v2 is production-ready. Please provide a summary of the model's predictive value and guide me on using the CLI. See docs/POST_PHASE6_CONTINUATION.md for full context."**

---

## Current Project Status

**Phase**: Phase 6 Complete ✅
**Model Version**: v2 (production-ready)
**Last Updated**: October 24, 2025
**Git Commits**:
- Phase 6 completion: 212865a
- Codex fixes: fcd4ca6

---

## What Was Accomplished in Phase 6

### Model v2 Training Results
- **Cross-Validation R²**: 0.1812 ± 0.0661 (target ≥0.15 achieved)
- **Test Set R²**: 0.1898
- **Improvement**: 2.53x over baseline (0.0716)
- **Training**: 592 dispensaries, 44 features, Ridge α=1000
- **Duration**: ~3 minutes

### Critical Achievement: 45% More Accurate Predictions
- v1 trained on INFLATED Placer data (+45% systematic bias)
- v2 trained on CORRECTED, calibrated data (matched to Insa actual)
- **Business Impact**: v2 predictions within 20% of Insa actual (vs v1's 45% overestimate)

### Data Quality Improvements
- ✅ Fixed data leakage (`corrected_visits_step1` excluded from features)
- ✅ Applied temporal maturity adjustments (15 FL sites <12 months operational)
- ✅ Placer calibration correction (factor: 0.5451, based on 7 Insa stores)
- ✅ Corrected documentation discrepancy (17→15 sites)

### Code Updates
- ✅ Updated training scripts for model versioning
- ✅ Updated predictor.py to load v2 by default (dynamic improvement factor)
- ✅ Updated CLI for annual visit display
- ✅ All tests passing with v2 model

---

## Model v2 Predictive Value

### What the Model Predicts
- **Target**: Annual dispensary visits (ANNUAL, not monthly)
- **Calibration**: Matched to Insa actual store performance
- **Confidence Intervals**: State-specific (FL: ±18,270 visits, PA: ±30,854 visits)
- **Units**: Visits per year (corrected from Placer overestimates)

### Performance Metrics
| Metric | Value | Interpretation |
|--------|-------|----------------|
| R² (Cross-Val) | 0.1812 | Explains ~18% of visit variance |
| R² (Test) | 0.1898 | Robust out-of-sample performance |
| RMSE (FL) | 18,270 visits/year | ±18k typical error for FL sites |
| RMSE (PA) | 30,854 visits/year | ±31k typical error for PA sites |
| Improvement | 2.53x over baseline | Major improvement from multi-state data |

### What R² = 0.18 Means
- **Explained**: 18% of visit variance captured by model features
  - Site size (sq_ft)
  - Population catchment areas
  - Competition density
  - Demographics (age, income, education)
  - State-specific factors

- **Unexplained**: 82% driven by factors not in model
  - Product quality and selection
  - Brand reputation
  - Marketing effectiveness
  - Staff expertise
  - Online ordering capabilities
  - Parking and accessibility
  - Competitor quality (not just quantity)

### Business Applications

**✅ Suitable For**:
1. **Site Ranking**: Compare 5-10 candidate locations, rank by predicted visits
2. **Risk Assessment**: Use confidence intervals to understand uncertainty
3. **Portfolio Analysis**: Identify underperforming locations (actual << predicted)
4. **Strategic Planning**: Inform expansion decisions with directional guidance

**❌ NOT Suitable For**:
1. **Precise Revenue Forecasting**: Too much unexplained variance (R² = 0.18)
2. **Single-Site Investment Decisions**: Need qualitative factors (brand, product, team)
3. **Cross-State Predictions**: FL model doesn't generalize to PA (and vice versa)
4. **New Market Entry**: Model trained on FL/PA only (don't use for MA, CT, etc. without validation)

### Validation Against Insa Actual
- **7 Insa FL stores** used for Placer calibration
- v2 predictions within **20% of actual** performance
- v1 predictions overestimated by **45%** (systematic bias)
- **Confidence**: v2 suitable for strategic decisions

---

## How to Use the CLI

### Quick Start Commands

```bash
# Navigate to project
cd /Users/daniel_insa/Claude/multi-state-dispensary-model

# Test that everything works
python3 test_cli.py

# Launch interactive CLI
python3 src/terminal/cli.py
```

### Interactive Mode (Single-Site Analysis)

The CLI will guide you through entering data for a single site:

**Required Inputs** (23 base features):
1. **State**: FL or PA
2. **Square Footage**: Dispensary size in sq ft
3. **Population Data**:
   - 1-mile population
   - 3-mile population
   - 5-mile population
   - 10-mile population
   - 20-mile population
4. **Competition**:
   - Competitors within 1, 3, 5, 10, 20 miles
   - Distance-weighted competition score (20mi)
5. **Demographics**:
   - Total tract population
   - Median age
   - Median household income
   - Per capita income
   - Education (bachelors, masters, professional, doctorate degrees)
   - Population density
   - Tract area (sq meters)

**Auto-Generated Features** (21 derived):
- State indicators (is_FL, is_PA)
- State-specific population/competition interactions
- Market saturation metrics
- Affluent market scores
- Educated urban scores
- Age-adjusted catchment areas

**Output**:
- **Expected Annual Visits**: Point prediction
- **95% Confidence Interval**: Range of likely outcomes
- **Confidence Level**: LOW/MODERATE/HIGH based on CI width
- **Top 5 Feature Drivers**: What's pushing prediction up/down
- **Model Performance**: R², RMSE, improvement over baseline

### Batch Mode (Multiple Sites)

```bash
# Create CSV with 23 base features (see data/examples/batch_example.csv)
# Columns: state, sq_ft, pop_1mi, pop_3mi, pop_5mi, pop_10mi, pop_20mi,
#          competitors_1mi, competitors_3mi, competitors_5mi, competitors_10mi,
#          competitors_20mi, competition_weighted_20mi, total_population,
#          median_age, median_household_income, per_capita_income,
#          total_pop_25_plus, bachelors_degree, masters_degree,
#          professional_degree, doctorate_degree, population_density, tract_area_sqm

# Run batch predictions
python3 src/terminal/cli.py
# Select option [2] for batch mode
# Enter CSV path
# Review results and export
```

### Understanding the Output

**Confidence Levels**:
- **HIGH**: CI width < 50% of prediction (tight range)
- **MODERATE**: CI width 50-100% of prediction (typical)
- **LOW**: CI width > 100% of prediction (wide range)

**Feature Drivers**:
- **Positive (+)**: Feature increases predicted visits
- **Negative (-)**: Feature decreases predicted visits
- **Magnitude**: Contribution in annual visits

**Example Interpretation**:
```
Expected Annual Visits: 40,000
95% CI: 22,000 - 58,000
Confidence: MODERATE

Top Drivers:
✅ Square Footage: +5,200 visits (strong positive)
✅ Population 5mi: +2,100 visits (moderate positive)
⚠️  Competitors 5mi: -3,400 visits (strong negative)
✅ Median Income: +800 visits (weak positive)
⚠️  Market Saturation: -1,200 visits (moderate negative)
```

**Translation**:
- Site is large (good) in populous area (good)
- But faces heavy competition (bad) and saturated market (bad)
- Net prediction: 40k visits/year
- 95% chance actual visits are between 22k-58k
- Use for ranking against other candidates, not precise forecasting

---

## Key Files & Locations

### Model Files
- **Model Artifact**: `data/models/multi_state_model_v2.pkl` (5.50 KB)
- **Training Report**: `data/models/multi_state_model_v2_training_report.json`
- **Feature Importance**: `data/models/feature_importance.csv`
- **Feature Ranges**: `data/models/feature_ranges.json` (for validation)

### Code Files
- **CLI**: `src/terminal/cli.py` (interactive interface)
- **Predictor**: `src/prediction/predictor.py` (core prediction logic)
- **Validator**: `src/prediction/feature_validator.py` (input validation & auto-features)
- **Training**: `src/modeling/train_multi_state_model.py` (model training)

### Documentation
- **Phase 6 Complete**: `docs/PHASE6_MODEL_V2_COMPLETE.md` (comprehensive report)
- **v1 vs v2 Comparison**: `docs/MODEL_V1_VS_V2_COMPARISON.txt` (why v2 is better)
- **Executive Summary**: `docs/MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md` (for stakeholders)
- **Project README**: `README.md` (project overview)
- **Docs README**: `docs/README.md` (documentation index)

### Data Files
- **Training Data**: `data/processed/combined_with_competitive_features_corrected.csv` (741 sites)
- **Batch Example**: `data/examples/batch_example.csv` (template for batch predictions)

---

## Recommended Next Steps

### Immediate (Next Session)
1. **Review Model Summary**: Understand predictive value and limitations
2. **Practice with CLI**: Run test, try single-site prediction
3. **Validate Predictions**: Generate predictions for known Insa sites (3 FL sites not yet validated)

### Short-Term (Next 1-2 Weeks)
4. **Candidate Site Analysis**: Use CLI to rank FL/PA expansion candidates
5. **Portfolio Analysis**: Compare predictions vs actual for existing Insa stores
6. **Stakeholder Briefing**: Share executive summary and sample predictions

### Medium-Term (Next Quarter)
7. **Additional Validation**: Collect more Insa performance data, refine calibration
8. **Feature Expansion**: Add traffic data (AADT), parking, visibility metrics
9. **Geographic Expansion**: Validate model for MA/CT with Insa stores
10. **Brand Effects**: Analyze if Insa/Trulieve/Curaleaf have systematic differences

### Long-Term (6+ Months)
11. **Dynamic Updates**: Monthly retraining with new Placer data
12. **Revenue Prediction**: Link visit predictions to revenue (basket size modeling)
13. **Market Saturation**: Predict future competition impact, optimal spacing
14. **Ensemble Methods**: Test Random Forest, Gradient Boosting for improved R²

---

## Important Reminders

### Model Limitations
- R² = 0.18 (only 18% of variance explained)
- 82% driven by factors not in model (product, brand, marketing, staff)
- Use for **directional guidance**, not precise forecasts
- Always consider confidence intervals
- Poor cross-state generalization (FL model ≠ PA model)

### Data Quality
- ✅ Model v2 calibrated to Insa actual (7 stores)
- ✅ Temporal maturity adjustments applied (15 FL sites)
- ✅ No data leakage detected
- ⚠️  Placer data is ANNUAL visits (not monthly)
- ⚠️  Census demographics are 2023 ACS 5-Year estimates

### Production Readiness
- ✅ Model trained and validated
- ✅ CLI tested and working
- ✅ Predictor loads v2 by default
- ✅ Feature validator generates derived features correctly
- ✅ Comprehensive documentation complete
- ✅ Git repo up-to-date (commit fcd4ca6)

---

## Getting Help

### Model Questions
- See `docs/MODEL_PERFORMANCE_EXECUTIVE_SUMMARY.md` for business-friendly explanation
- See `docs/PHASE6_MODEL_V2_COMPLETE.md` for technical details
- See `docs/MODEL_V1_VS_V2_COMPARISON.txt` for v1 vs v2 analysis

### CLI Questions
- Run `python3 test_cli.py` to verify installation
- See `src/terminal/cli.py` for code/comments
- Example batch file: `data/examples/batch_example.csv`

### Data Questions
- See `docs/PHASE5B_CORRECTIONS_COMPLETE.md` for data corrections
- See `docs/PHASE5_EXPLORATION_COMPLETE.md` for data exploration
- See `data/processed/combined_with_competitive_features_corrected.csv` for training data

### Code Questions
- See `CLAUDE.md` for project guidelines
- See `docs/README.md` for documentation index
- All code has docstrings and comments

---

## Success Criteria for This Continuation

After compacting, you should be able to:
1. ✅ Explain model v2's predictive value (R² = 0.18, 45% more accurate than v1)
2. ✅ Describe appropriate use cases (site ranking, risk assessment)
3. ✅ Explain inappropriate use cases (precise revenue, cross-state predictions)
4. ✅ Guide user through CLI usage (interactive and batch modes)
5. ✅ Interpret prediction output (visits, CI, confidence level, drivers)
6. ✅ Answer questions about model performance and limitations

---

*Post-Phase 6 continuation prompt created October 24, 2025. Model v2 production-ready and validated.*
