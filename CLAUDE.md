# CLAUDE.md - Multi-State Dispensary Model Project Guidelines

## 🎯 CRITICAL PROJECT PRINCIPLES

### **Data Integrity - HIGHEST PRIORITY**
- **NEVER USE SYNTHETIC DATA** without explicit approval from Daniel
- **NEVER** use geocoding estimates - require actual coordinates
- **ALWAYS** use verified real data from legitimate sources (Census, DOT, Placer.ai, etc.)
- **IF REAL DATA IS UNAVAILABLE** - Ask for explicit approval before using ANY estimates

### **Focus on Requested Changes Only**
- Change only what is specifically requested
- Don't "improve" working functionality unless asked
- Ask before making changes outside the specific request
- Build incrementally, testing each component before moving to the next

---

## Project Overview

**Multi-State Dispensary Prediction Model** - Enhanced site analysis for Pennsylvania and Florida combining demographic, geographic, and traffic data to predict dispensary performance with significantly improved accuracy through larger training datasets.

### Current Status (October 2025)
- **Status**: Production Ready ✅
- **Model Version**: v3.0 (State-Specific Models)
  - Florida: Ridge Regression (R² = 0.0685, +42.8% improvement)
  - Pennsylvania: Random Forest (R² = 0.0756, from negative to positive!)
- **Training Data**: 741 dispensaries across PA & FL
- **Interface**: Complete terminal CLI with report generation and multi-site analysis
- **Key Features**:
  - Coordinate-based input (3-4 inputs vs 23 manual features)
  - Multi-site analysis (up to 5 sites per session)
  - Professional report generation (HTML/CSV/TXT/JSON) with v3.0 scoring
  - Site performance scoring (1-5 scale with percentile rankings)
  - State-specific branding and benchmarks
  - Automatic state routing (zero user impact)

---

## Core System Architecture

### **Data Integration Pipeline**
- Placer data consolidation for PA & FL (~750 dispensaries)
- Census demographics integration at tract level
- State regulator data for complete competitive landscape
- Insa actual performance data for validation benchmark

### **Enhanced Feature Engineering**
- Multi-radius population analysis (1mi, 3mi, 5mi, 10mi)
- Distance-weighted competition metrics
- Market saturation indicators (dispensaries per capita)
- Demographic profiles (age, income, education)
- State-specific factors and multipliers
- Traffic/accessibility data where available

### **Model Development**
- State-specific models optimized for within-state predictions (v3.0)
  - Florida: Ridge Regression with 31 features
  - Pennsylvania: Random Forest with 31 features
- Automatic state routing based on location
- Geographic cross-validation with state-based splits
- Confidence intervals and uncertainty quantification (±75% cap)
- Validation against Insa actual performance
- Site performance scoring (1-5 scale) based on percentile rankings

---

## Data Sources & Standards

### **Verified Data Sources**
- **Placer Data**: Visit estimates, coordinates, square footage (~750 dispensaries)
- **Census Data**: Demographics by tract (PA & FL)
- **State Regulator Data**: Complete licensing and competitive data
- **Insa Performance**: Actual visit data from FL, MA, CT stores
- **Traffic Data**: AADT where available by state

### **Data Quality Requirements**
- All coordinates verified within state boundaries
- No synthetic estimates without explicit approval
- Comprehensive validation at each processing step
- Clear documentation of all transformations
- Backup of original data before any processing

---

## Development Guidelines

### **Code Quality Standards**
- Follow existing PA model patterns for consistency
- Use descriptive variable names with snake_case
- Include docstrings with clear parameter descriptions
- Add try-catch blocks for external data operations
- Print progress updates for long-running operations

### **File Management**
- Use descriptive names: `multi_state_dispensaries.csv` not `output.csv`
- Version important files with dates when updated
- Document schema and source for all datasets
- Keep original files in `data/raw/` untouched
- Store processed files in `data/processed/`

### **Testing Approach**
- Start with small datasets before full processing
- Validate outputs make logical business sense
- Compare results against PA model patterns
- Cross-validate between PA and FL data
- Document any unexpected findings

---

## Business Context

### **Multi-State Modeling Goals**
- **Primary**: Significantly improved predictive power through larger dataset
- **Secondary**: Cross-state insights and universal success factors
- **Validation**: Performance benchmarking against Insa actual stores
- **Application**: PA & FL site selection and portfolio optimization

### **Success Metrics**
- **Statistical**: Target R² > 0.15 (major improvement over 0.0716)
- **Business**: Accurate site ranking and risk assessment
- **Validation**: Strong correlation with Insa actual performance
- **Usability**: Clean terminal interface matching PA model standards

---

## Recent Enhancements (October 2025)

### **On-the-Fly Census Tract Fetching**
- System automatically fetches missing census tracts from Census API
- Handles all PA/FL locations (not just pre-loaded tracts)
- Safe handling of None values when Census data incomplete
- Cached for performance
- See: `docs/SESSION_SUMMARY_2025_10_28_CENSUS_TRACT_FIX.md`

### **Extreme Value Warning System**
- Validates features against training data ranges
- Prompts user for approval when values extreme
- Distinguishes between extreme (requires approval) and out-of-range (informational)
- Batch mode flags sites with warnings in output CSV
- Transparent about prediction reliability

### **Confidence Interval Improvements (v2.1)**
- Prediction-proportional RMSE scaling (smaller predictions = narrower intervals)
- ±75% cap for business usability (prevents unusably wide intervals)
- Transparent cap notifications in all outputs (HTML/CSV/TXT/CLI)
- Reduced interval width from 222% → 150% of prediction
- Lower bounds now meaningful (12k vs 0 for 50k prediction)
- See: `docs/SESSION_SUMMARY_2025_10_28_CI_IMPROVEMENTS.md`

### **State-Specific Models v3.0** (October 28, 2025)
- Separate models for FL and PA optimized for within-state predictions
- Florida: Ridge Regression (R² = 0.0685, +42.8% improvement)
- Pennsylvania: Random Forest (R² = 0.0756, from negative to positive!)
- Automatic state routing based on location (zero user impact)
- Both states now usable for comparative ranking
- See: `docs/SESSION_SUMMARY_2025_10_28_STATE_SPECIFIC_V3.md`

### **Report System v3.0** (October 29, 2025)
- All reports updated to v3.0 version numbering
- Site performance scoring (1-5 scale) matching PA model format
  - 5.0: Exceptional (Top 10%), 4.0: Above Average (70-90th percentile)
  - 3.0: Average (30-70th percentile), 2.0: Below Average (10-30th percentile)
  - 1.0: Poor (Bottom 10%)
- Color-coded circular score badges in HTML reports
- Enhanced footer with state-specific performance metrics and guidance
- CSV properly sorted by rank
- See: `docs/SESSION_SUMMARY_2025_10_29_REPORT_V3_IMPROVEMENTS.md`

---

## Project Structure

```
multi-state-dispensary-model/
├── data/
│   ├── raw/                    # Original datasets (git-ignored)
│   ├── processed/              # Cleaned, integrated data
│   └── models/                 # Trained model artifacts
├── src/
│   ├── data_integration/       # Data merging and consolidation
│   ├── feature_engineering/    # Population, competition, demographic analysis
│   ├── modeling/               # Training, validation, prediction
│   └── reporting/              # Terminal interface and output generation
├── sandbox/                    # Experimentation and development
├── tests/                      # Data validation and model tests
└── docs/                       # Methodology, findings, learnings
```

---

## Communication Guidelines

### **Progress Updates**
- Provide regular updates on data processing steps
- Explain any unexpected results or data quality issues
- Break complex tasks into clear, manageable steps
- Document lessons learned for future reference

### **Technical Explanations**
- Define terms like census tracts, AADT, spatial analysis
- Provide context explaining WHY not just WHAT
- Use concrete examples from the dispensary industry
- Keep explanations clear but comprehensive

---

## Task Management

### **Current Status**: All Phases Complete ✅

**Completed Work**:
1. ✅ Data Integration - 741 training dispensaries with competitive landscape
2. ✅ Census Integration - 7,624 census tracts with full demographics
3. ✅ Feature Engineering - 44 features (23 base + 21 derived)
4. ✅ Model Development - Model v2 with corrected data (R² = 0.1812)
5. ✅ CLI Automation - Coordinate-based input (3-4 inputs)
6. ✅ Report Generation - Professional HTML/CSV/TXT/JSON reports
7. ✅ Multi-Site Analysis - Up to 5 sites per session with comparison

### **System Ready For**:
- Production use for PA & FL site analysis with v3.0 state-specific models
- Client presentations with professional reports (HTML/CSV/TXT/JSON)
- Multi-site comparisons and portfolio planning (up to 5 sites)
- Site performance scoring and percentile rankings (1-5 scale)
- Data export for further analysis (CSV properly sorted)
- Within-state comparative ranking (FL and PA both usable)

---

## Error Prevention & Quality Assurance

### **Common Pitfalls to Avoid**
- **Coordinate Errors**: Validate all coordinates within state boundaries
- **Data Leakage**: Properly separate training and validation data
- **State Mixing**: Handle PA vs FL differences appropriately
- **Scale Issues**: Normalize features appropriately for multi-state training

### **Quality Checks**
- Verify expected record counts after joins and filters
- Check calculated values against business logic
- Ensure model performance exceeds PA baseline
- Validate predictions against Insa actual performance

---

## Version Control & Documentation

### **Git Standards**
- Frequent commits with clear, descriptive messages
- Feature branches for major development work
- Never commit raw data files (use .gitignore)
- Document all major changes in commit messages

### **Documentation Requirements**
- README files in all major directories
- Code comments for complex business logic
- Methodology documentation for all modeling decisions
- Performance tracking and comparison to baseline

---

## Summary for AI Assistant

**Primary Function**: Develop multi-state dispensary prediction model building on PA v3.1 foundation
**Core Principle**: Real data only - no synthetic estimates without explicit approval
**Current Phase**: Data integration and consolidation (Phase 1 of 4)
**Success Target**: R² > 0.15 through enhanced features and larger dataset (~750 dispensaries)
**Validation Standard**: Performance benchmarking against Insa actual store data
**Interface Goal**: Enhanced terminal interface maintaining PA model's proven usability

This project extends INSA's proven dispensary site analysis capabilities to multi-state operations with significantly improved predictive accuracy through advanced data integration and feature engineering.