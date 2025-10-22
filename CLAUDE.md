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
- **Phase**: Data Integration (Phase 1 of 4)
- **Architecture**: Building on proven PA Dispensary Model v3.1 foundation
- **Target Performance**: R² > 0.15 (significant improvement over PA model's 0.0716)
- **Training Data**: ~750 dispensaries across PA & FL
- **Interface**: Enhanced terminal interface with multi-state capabilities

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
- Enhanced Ridge regression with state interaction terms
- Ensemble methods testing for improved performance
- Geographic cross-validation with state-based splits
- Confidence intervals and uncertainty quantification
- Validation against Insa actual performance

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

### **Current Phase**: Data Integration
1. **Data Collection**: Consolidate Placer data for PA & FL
2. **Census Integration**: Add demographic data at tract level
3. **Regulator Data**: Complete competitive landscape
4. **Validation Data**: Integrate Insa performance benchmarks
5. **Quality Pipeline**: Comprehensive validation and cleaning

### **Upcoming Phases**
- **Phase 2**: Enhanced feature engineering with multi-radius analysis
- **Phase 3**: Model development with state interaction terms
- **Phase 4**: Interface adaptation and enhanced reporting system

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