# Bug Fix - Address/AADT Not Reaching Reports

**Date:** October 28, 2025  
**Severity:** High (data loss)  
**Status:** Fixed ✅

## Issues Identified by Code Review

### Issue 1: HIGH - Address/AADT Dropped in Interactive Mode

**Problem:** Address and AADT were collected in `prompt_coordinates_only()` but never made it to reports or summaries.

**Root Cause:** The `_prepare_result_dict()` method copied `base_features` (which come from the calculator) but didn't copy `address` and `aadt` from the `coords` dictionary.

**Impact:** Users entering addresses and AADT saw them disappear. All reports showed only coordinates.

**Fix Applied:**
```python
# src/terminal/cli.py:928-939
# Before:
result_dict.update({
    'state': state,
    'latitude': coords['latitude'],
    'longitude': coords['longitude'],
    'predicted_visits': result['prediction'],
    ...
})

# After:
result_dict.update({
    'state': state,
    'latitude': coords['latitude'],
    'longitude': coords['longitude'],
    'address': coords.get('address'),      # ← ADDED
    'aadt': coords.get('aadt'),            # ← ADDED
    'predicted_visits': result['prediction'],
    ...
})
```

---

### Issue 2: MEDIUM - Address/AADT Omitted in Batch CSV Mode

**Problem:** Batch mode completely ignored address, latitude, longitude, and AADT from input CSV files.

**Root Cause:** The `result_row` dictionary in batch processing only extracted model features, not contextual metadata from the input CSV.

**Impact:** Input CSVs with address/AADT/coordinates had those fields stripped in output, making site identification impossible.

**Fix Applied:**
```python
# src/terminal/cli.py:390-410
# Before:
result_row = {
    'site_id': idx + 1,
    'state': state,
    'sq_ft': base_features['sq_ft'],
    ...
}

# After:
result_row = {
    'site_id': idx + 1,
    'state': state,
    'address': row.get('address', ''),      # ← ADDED
    'latitude': row.get('latitude', ''),    # ← ADDED
    'longitude': row.get('longitude', ''),  # ← ADDED
    'aadt': row.get('aadt', ''),            # ← ADDED
    'sq_ft': base_features['sq_ft'],
    ...
}
```

Also fixed error handling case (lines 418-426) to preserve these fields even when predictions fail.

---

## Testing

Both fixes validated with unit tests:

```
TEST 1: Interactive Mode - _prepare_result_dict
✅ PASS: Address correctly included in result_dict
✅ PASS: AADT correctly included in result_dict

TEST 2: Batch Mode - result_row construction
✅ PASS: address correctly included
✅ PASS: latitude correctly included
✅ PASS: longitude correctly included
✅ PASS: aadt correctly included

✅ ALL TESTS PASSED
```

---

## Files Modified

- `src/terminal/cli.py`:
  - Line 933-934: Added address/AADT to `_prepare_result_dict()` result
  - Line 393-396: Added address/lat/lon/AADT to batch mode `result_row`
  - Line 421-424: Added same fields to batch error handling

---

## Verification Checklist

- ✅ Interactive mode: address/AADT flow from input → coords → results → reports
- ✅ Batch mode: address/lat/lon/AADT preserved from CSV → output CSV
- ✅ Reports display address in titles and tables when available
- ✅ CSV exports include all contextual fields
- ✅ Backward compatible (optional fields default to None/'')
- ✅ Error cases preserve contextual data

---

## Lessons Learned

1. **Always trace data flow end-to-end** - Collecting data is only half the battle; ensure it flows all the way through.

2. **Test both code paths** - Interactive and batch modes can have different data flows.

3. **Code review catches what testing misses** - Manual testing of interactive mode might miss batch mode issues.

---

## Credit

Issues identified by Codex code review. Fixes validated and deployed.
