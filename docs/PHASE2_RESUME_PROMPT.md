# Phase 2 Resume Prompt - Census Demographics Integration

**Use this prompt after compacting the chat to begin Phase 2**

---

I'd like to resume work on my Multi-State Dispensary Model project.

We just completed **Phase 1 (Data Integration)** including a comprehensive code review and fixes. I'm now ready to begin **Phase 2 (Census Demographics Integration)**.

## Phase 1 Summary - What's Been Completed ✅

### Data Foundation
- **741 training-eligible dispensaries** across PA & FL (98.8% of 750 target)
- **937 total dispensaries** for comprehensive competitive landscape
- **79.1% training data coverage** (741/937 dispensaries have visit data)
- 100% coordinate coverage for all training dispensaries

### Data Quality Improvements
- Enhanced address matching with composite scoring (60% addr + 25% city + 15% ZIP)
- Average match confidence: 96.3 (FL), 97.7 (PA)
- Cannabis brand whitelist filtering (prevents false positives like "Surterra Wellness")
- Automated coordinate boundary validation
- Comprehensive test suite for regression prevention

### Key Deliverables
- **Florida**: 735 total dispensaries (590 training-eligible, 145 competition-only)
- **Pennsylvania**: 202 total dispensaries (151 training-eligible, 40 competition-only, 11 Act 63 provisional)
- Production-ready data integration pipeline with tests
- Full documentation in `/docs/PHASE1_COMPLETION_REPORT.md` and `/docs/CODE_REVIEW_FIXES.md`

### Repository
- GitHub: https://github.com/daniel-sarver/multi-state-dispensary-model
- All Phase 1 work committed and pushed
- Data files: `/data/processed/FL_combined_dataset_current.csv` and `PA_combined_dataset_current.csv`

---

## Phase 2 Objectives - Census Demographics Integration

### Goal
Add demographic features to our **741 training-eligible dispensaries** to enhance model predictive power beyond the PA model baseline (R² = 0.0716). Target: R² > 0.15.

### Scope
Pull demographic data for all dispensaries where `has_placer_data: True` using the US Census Bureau API.

### Required Demographic Features

**Population Analysis** (Multiple Radii):
- 1-mile radius population
- 3-mile radius population
- 5-mile radius population
- 10-mile radius population

**Demographic Variables** (Census Tract Level):
- Age distribution (median age, % 21-65, % seniors)
- Household income (median household income)
- Per capita income
- Education levels (% bachelor's degree or higher)
- Population density (people per square mile)

### Technical Approach

**Data Source**:
- US Census Bureau API (public government data - acceptable to pull automatically)
- Use American Community Survey (ACS) 5-year estimates for reliability
- Census tract-level data based on dispensary coordinates

**Implementation Requirements**:
1. **Census Tract Identification**: Use coordinates to identify census tract for each dispensary
2. **Multi-Radius Aggregation**: Calculate population within each buffer distance (1/3/5/10 mi)
3. **Demographic Integration**: Merge census variables with combined datasets
4. **Data Quality Validation**: Comprehensive validation and null-handling strategy
5. **Documentation**: Clear methodology and data source documentation

**Data Integrity Standards** (CRITICAL):
- ✅ Census API is public government data - acceptable to pull automatically
- ✅ Use real census data only - no synthetic estimates
- ✅ Comprehensive validation at each step
- ✅ Clear documentation of all transformations
- ✅ Handle missing data appropriately (flag, don't fabricate)

### Expected Deliverables

**Code**:
- Census data collection script (`src/feature_engineering/collect_census_data.py`)
- Integration script to merge census data with combined datasets
- Comprehensive logging and progress tracking

**Data Outputs**:
- Enhanced combined datasets with demographic features
- Census data summary/quality report (JSON format)
- Documentation of census methodology and variables

**Testing**:
- Unit tests for census data collection
- Validation of census tract identification
- Boundary checking for population aggregation

**Documentation**:
- Phase 2 completion report
- Census data dictionary (variable definitions and sources)
- Data quality metrics and coverage analysis

### Key Questions to Consider

**Q: Which census variables should we prioritize?**
A: Start with population (all radii), median household income, median age, and population density. Add education and per capita income if time permits.

**Q: How do we handle dispensaries near state boundaries?**
A: Multi-radius buffers may cross state lines - aggregate census tracts from both states within buffer.

**Q: What if census data is missing for a tract?**
A: Flag the record with `census_data_complete: False`, document the gap, but keep the dispensary in the dataset. Never fabricate data.

**Q: Should we pull current census or historical?**
A: Use most recent ACS 5-year estimates (typically 2019-2023 or 2020-2024 depending on release). Document the vintage.

**Q: What about the 196 competition-only dispensaries?**
A: They don't have coordinates, so skip census data for now. They're only needed for competitive distance calculations later.

### Implementation Steps

1. **Setup & Research** (~1 hour)
   - Review US Census Bureau API documentation
   - Identify required API endpoints (geocoding, ACS variables)
   - Set up Census API access (may need API key)
   - Test API calls with sample coordinates

2. **Census Tract Identification** (~2 hours)
   - Build geocoding function to get census tract from lat/lon
   - Test on sample of FL and PA dispensaries
   - Validate tract boundaries make sense

3. **Multi-Radius Population Calculation** (~3 hours)
   - Implement buffer generation (1/3/5/10 mile radii)
   - Identify all census tracts intersecting each buffer
   - Aggregate population within each radius
   - Handle edge cases (water bodies, state boundaries)

4. **Demographic Data Collection** (~2 hours)
   - Pull ACS variables for each census tract
   - Merge demographic data with dispensary records
   - Create derived features (population density, age groups)

5. **Integration & Validation** (~2 hours)
   - Merge census data with combined datasets
   - Comprehensive data quality validation
   - Generate summary reports
   - Update documentation

6. **Testing** (~1 hour)
   - Write unit tests for census functions
   - Validate sample of results manually
   - Check for edge cases and null handling

**Estimated Total Time**: 1-2 days

### Success Criteria

- ✅ Census data successfully collected for all 741 training dispensaries
- ✅ Multi-radius population analysis complete (1/3/5/10 mi)
- ✅ Demographic variables integrated into combined datasets
- ✅ Data quality validated (no fabricated data, nulls properly flagged)
- ✅ Comprehensive documentation of methodology and sources
- ✅ All changes committed to Git with clear commit messages

### Files to Reference

**Phase 1 Documentation**:
- `/docs/PHASE1_COMPLETION_REPORT.md` - Complete Phase 1 summary
- `/docs/CODE_REVIEW_FIXES.md` - Enhancements and fixes (+98 dispensaries recovered)
- `/docs/CONTINUATION_PROMPT.md` - Original Phase 1→2 transition context

**Data Files**:
- `/data/processed/FL_combined_dataset_current.csv` - 735 FL dispensaries
- `/data/processed/PA_combined_dataset_current.csv` - 202 PA dispensaries

**Code**:
- `/src/data_integration/create_combined_datasets.py` - Phase 1 pipeline (reference for patterns)
- `/tests/test_data_integration.py` - Testing patterns to follow

**Project Guidelines**:
- `/CLAUDE.md` - Critical project principles (data integrity, real data only)
- `/requirements.txt` - Current dependencies

### Important Reminders

**Data Integrity** (HIGHEST PRIORITY):
- NEVER use synthetic or estimated census data
- ALWAYS use verified real data from US Census Bureau API
- If real data is unavailable for a dispensary, flag it clearly
- Document all data sources and methodology

**Code Quality**:
- Follow existing patterns from Phase 1
- Write tests for critical functionality
- Comprehensive logging and error handling
- Clear, descriptive variable names

**Git Workflow**:
- Frequent commits with descriptive messages
- Test code before committing
- Push regularly to remote repository
- Document significant changes

---

## Ready to Begin!

Please review the Phase 1 documentation linked above, then let's start Phase 2 by:

1. Researching the US Census Bureau API and identifying the required endpoints
2. Planning the census data collection architecture
3. Building the census tract identification system
4. Implementing multi-radius population analysis
5. Integrating demographic features into our combined datasets

Let me know when you've reviewed the materials and are ready to proceed with Phase 2: Census Demographics Integration!

---

*Project: Multi-State Dispensary Prediction Model*
*Current Phase: Phase 2 - Census Demographics Integration*
*GitHub: https://github.com/daniel-sarver/multi-state-dispensary-model*
