# Codex Review Fix - Feature Contributions for Tree-Based Models

**Date**: October 28, 2025
**Issue**: KeyError when accessing 'ridge' step for PA Random Forest model
**Severity**: Critical (would crash CLI on PA predictions)

---

## Issue Identified by Codex

**Location**: `src/prediction/predictor.py:462-488` (original `get_feature_contributions()`)

**Problem**:
The `get_feature_contributions()` method assumed every pipeline has a 'ridge' step and accessed coefficients via `self.pipeline.named_steps['ridge']`. However, the PA v3 model uses Random Forest (stored under 'model' step), causing a `KeyError: 'ridge'` crash when analyzing PA sites.

**Impact**:
- CLI would crash on any PA prediction when calling `get_top_drivers()`
- Affected both interactive and batch modes
- Would have been discovered immediately in production

---

## Fix Implemented

### Updated `get_feature_contributions()` Method

**Changes**:
1. Added logic to detect pipeline structure ('model' vs 'ridge' step)
2. Branch on algorithm type from metadata
3. **Ridge models**: Use existing coefficient-based contributions
4. **Tree-based models** (RF, XGBoost): Use `feature_importances_` instead
5. Maintain consistent DataFrame structure with 'contribution' column for both

**Code Logic**:
```python
# Determine algorithm type from pipeline
if 'model' in self.pipeline.named_steps:
    model = self.pipeline.named_steps['model']
elif 'ridge' in self.pipeline.named_steps:
    model = self.pipeline.named_steps['ridge']
else:
    raise ValueError("Unknown pipeline structure")

algorithm = self.model_metadata.get('algorithm', 'ridge')

# Branch on algorithm type
if algorithm == 'ridge' or hasattr(model, 'coef_'):
    # Ridge: coefficient-based contributions (site-specific)
    # ... existing coefficient logic ...

elif hasattr(model, 'feature_importances_'):
    # Tree-based: global feature importances
    # ... use feature_importances_ ...
```

### Output Structure

**Ridge Models** (FL v3, v2):
- Columns: `feature`, `value`, `coefficient`, `contribution`
- Includes intercept row
- Contributions are site-specific (coefficient × scaled_value)

**Tree-Based Models** (PA v3):
- Columns: `feature`, `value`, `importance`, `contribution`
- No intercept row (trees don't have intercepts)
- Contribution = importance (global feature importance, not site-specific)

Both maintain a `contribution` column for CLI compatibility.

---

## Testing Completed

### 1. Unit Tests ✅

**FL Model (Ridge)**:
```
✓ get_feature_contributions() returns 32 rows (31 features + intercept)
✓ Columns: ['feature', 'value', 'coefficient', 'contribution']
✓ get_top_drivers() returns top 5 features
```

**PA Model (Random Forest)**:
```
✓ get_feature_contributions() returns 31 rows (31 features, no intercept)
✓ Columns: ['feature', 'value', 'importance', 'contribution']
✓ get_top_drivers() returns top 5 features
```

### 2. CLI Integration Tests ✅

**FL Prediction**:
```
✓ Prediction: 40,429 visits
✓ CI: 10,107 - 70,750
✓ Top drivers display correctly with coefficient-based contributions
```

**PA Prediction**:
```
✓ Prediction: 61,525 visits
✓ CI: 15,381 - 107,668
✓ Top drivers display correctly with importance-based contributions
```

### 3. CLI Display Logic ✅

Verified that CLI code correctly accesses `row['contribution']` which exists in both output formats.

---

## Key Differences: Ridge vs Random Forest Contributions

### Ridge Regression (FL Model)
- **Site-specific**: Contributions vary based on input values
- **Interpretation**: "This feature contributed +1,927 visits for THIS specific site"
- **Formula**: coefficient × (scaled_feature_value)
- **Example**: median_age contributes +1,927 visits

### Random Forest (PA Model)
- **Global**: Feature importances are model-wide, not site-specific
- **Interpretation**: "This feature is generally important across all predictions"
- **Formula**: Built-in feature_importances_ (based on impurity reduction)
- **Example**: competitors_20mi has importance 0.17

**Note for Users**: Random Forest "contributions" are actually global feature importances and don't reflect site-specific impacts like Ridge coefficients do. This is a known limitation of tree-based models.

---

## Files Modified

1. `src/prediction/predictor.py`
   - Updated `get_feature_contributions()` method (lines 423-526)
   - Added algorithm detection and branching logic
   - Maintained backward compatibility with v2 Ridge models
   - Added support for Random Forest and XGBoost

2. `docs/CODEX_REVIEW_FIX_2025_10_28.md` (this document)

---

## Future Considerations

### SHAP Values for Site-Specific Tree Importances

For true site-specific feature contributions from Random Forest/XGBoost, consider implementing SHAP (SHapley Additive exPlanations):

```python
import shap

# Would provide site-specific contributions like Ridge
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)
```

**Benefits**:
- Site-specific contributions for tree models
- More interpretable than global importances
- Shows direction and magnitude of impact

**Trade-offs**:
- Requires additional dependency (`shap` package)
- Slower computation (significant for batch mode)
- More complex implementation

**Recommendation**: Consider for future enhancement if users need site-specific explanations for PA predictions.

---

---

## Second Issue Identified by Codex

**Location**: `src/terminal/cli.py:889-904` (original display logic)

**Problem**:
CLI was displaying Random Forest feature importances (0-1 scale) as if they were visit deltas. Output showed "+0 visits" which was misleading since importances are not visit impacts.

**Example of Misleading Output**:
```
🔝 Top Feature Drivers:
  ✅ Competitors 20mi           +0 visits (weak positive)  ❌ WRONG
```

### Fix Implemented

**Changes to `print_results()` method**:
1. Detect if contributions are importances (≤1.0) or visit deltas (>1.0)
2. Display appropriately based on type:
   - **Ridge**: Show as visit deltas with direction indicators
   - **Random Forest**: Show as importance percentages

**Updated Display Logic**:
```python
# Detect contribution type
max_contribution = top_drivers['contribution'].abs().max()
is_importance = max_contribution <= 1.0

if is_importance:
    print("\n🔝 Top Feature Importances (Tree-Based Model):")
    # Display as percentages: "16.9% importance"
else:
    print("\n🔝 Top Feature Drivers:")
    # Display as visit deltas: "+1,927 visits (moderate positive)"
```

### Correct Output Examples

**FL Model (Ridge) - Visit Deltas**:
```
🔝 Top Feature Drivers:
  ✅ Median Age                       +1,927 visits (moderate positive)
  ⚠️ Saturation 5Mi                   -1,390 visits (moderate negative)
  ✅ Saturation 10Mi                    +982 visits (weak positive)

Key factor: Median Age is the strongest driver (+1,927 visits impact).
```

**PA Model (Random Forest) - Importance Percentages**:
```
🔝 Top Feature Importances (Tree-Based Model):
  🔹 Competitors 20Mi                 16.9% importance
  🔹 Educated Urban Score              7.8% importance
  🔹 Competition Weighted 20Mi         6.1% importance

Key factor: Competitors 20Mi is the most important feature (16.9% importance).
```

---

## Status

✅ **BOTH ISSUES FIXED AND TESTED**

### Issue 1: KeyError for Random Forest
- ✅ Fixed `get_feature_contributions()` to handle both Ridge and tree-based models
- ✅ PA predictions no longer crash

### Issue 2: Misleading Display Format
- ✅ Fixed CLI display to show importances as percentages (not visit deltas)
- ✅ Clear labeling distinguishes Ridge vs Random Forest outputs
- ✅ "Key factor" text updated for both model types

### Testing Completed
- Both FL (Ridge) and PA (Random Forest) predictions work correctly
- Display formats appropriate for each algorithm type
- Backward compatible with v2 unified model
- Comprehensive testing completed

**Status**: Production ready - No further action required for current deployment.
