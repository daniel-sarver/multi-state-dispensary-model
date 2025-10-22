# Dataset Analysis - Fresh Data from Daniel

**Analysis Date**: October 22, 2025
**Status**: Fresh datasets received and analyzed

## Dataset Overview

### 🎯 **Excellent Coverage Achieved:**
- **Total Placer Records**: 903 dispensaries (FL: 714 + PA: 189)
- **Total Regulator Records**: 950 dispensaries (FL: 734 + PA: 205 final + 10 Act 63)
- **Validation Data**: 18 Insa stores with actual vs Placer comparison

## Individual Dataset Analysis

### 1. Florida Placer Data (`FL_Placer Data_Oct 1, 2024-Sep 30, 2025_10.22.25.csv`)
**Records**: 714 dispensaries
**Time Period**: Oct 1, 2024 - Sep 30, 2025
**Quality**: Fresh, comprehensive Placer extract

**Key Fields Available**:
- Property Name, Address, City, State, Zip Code
- Latitude, Longitude (high precision coordinates)
- Visits (annual), Square Footage, Visits per Sq Ft
- Chain information (Chain Name, Chain ID)
- Market data (DMA, CBSA information)

**Data Quality Notes**:
- ⚠️  **Includes hemp/CBD stores** - requires filtering
- ✅ Complete visit and coordinate data
- ✅ Standard Placer format for easy processing

**Example Record**:
- Trulieve Orlando: 260,785 visits, 3,424 sq ft
- Curaleaf Spring Hill: 193,812 visits, 2,213 sq ft

### 2. Pennsylvania Placer Data (`PA_Placer Data_Oct 1, 2024-Sep 30, 2025_10.22.csv`)
**Records**: 189 dispensaries
**Time Period**: Oct 1, 2024 - Sep 30, 2025
**Quality**: Fresh, comprehensive PA extract

**Key Fields Available**:
- Same structure as FL data
- Complete visit and coordinate coverage
- Chain and market information

**Example Record**:
- Ascend Cannabis Scranton: 394,345 visits, 11,592 sq ft
- Organic Remedies Enola: 270,651 visits, 5,074 sq ft

### 3. Florida Regulator Data (`FL_Regulator License Data_Final License_10.22.25.csv`)
**Records**: 734 licensed dispensaries
**Source**: Official FL regulator list (pulled today)
**Quality**: Complete competitive landscape

**Fields Available**:
- Company Name, Address, City, Zip Code, County
- ⚠️  **Missing**: Coordinates, opening dates, license details

**Usage Strategy**:
- **Competition Analysis**: Use for complete competitor counting
- **Cross-Reference**: Validate Placer data coverage
- **Market Analysis**: Full FL competitive landscape

### 4. Pennsylvania Regulator Data (`PA_Regulator License Data_Final License_10.22.25.csv`)
**Records**: 205 licensed dispensaries
**Source**: PA DOH official list
**Quality**: Comprehensive with operational details

**Rich Field Set**:
- Medical marijuana available date, Open date
- Product availability status
- Dispensary name, Full address
- Phone, Website
- ⚠️  **Missing**: Coordinates (will need geocoding or matching)

**Key Advantages**:
- **Opening dates available** - can determine >1 year operation
- **Operational status** - active vs inactive dispensaries

### 5. Pennsylvania Act 63 Licenses (`PA_Regulator License Data_Act 63 Licenses_10.22.25.csv`)
**Records**: 10 provisional licenses
**Purpose**: Future competition consideration

**Fields Available**:
- Applicant Name, Permit Number, Region
- Facility Name, Type, Address, County

**Strategic Use**:
- **Future Competition**: Include in competitor radius analysis
- **Market Saturation**: Consider for market opportunity assessment
- **Model Enhancement**: Flag areas with pending competition

### 6. Insa Validation Data (`Insa Store Data_5.1.24-4.30.25.csv`)
**Records**: 18 Insa stores
**Purpose**: Model validation and Placer accuracy assessment
**Time Period**: May 1, 2024 - April 30, 2025

**Critical Validation Fields**:
- State, Site Name, Address
- Revenue, Units Sold, Average Transaction Value
- **Actual Visits** vs **Placer Visits** comparison

**Key Validation Insights**:
- Direct comparison of actual vs Placer estimates
- Multiple states: CT, FL (primary validation markets)
- Revenue and operational metrics for business context

## Data Integration Strategy

### Dual-Dataset Approach (As Planned)
1. **Complete Competitive Landscape**:
   - FL: 734 regulator + 10 Act 63 = 744 total competitors
   - PA: 205 regulator dispensaries for full competition analysis

2. **Training Dataset** (Placer subset):
   - FL: 714 dispensaries (after hemp/CBD filtering)
   - PA: 189 dispensaries
   - Total: ~900 dispensaries for training (exceeds ~750 target)

### Critical Processing Tasks

#### 1. Hemp/CBD Store Filtering (FL Priority)
**Method**: Filter FL Placer data using:
- Sub Category = "Marijuana Dispensary" (keep)
- Category = "Medical & Recreational Cannabis Dispensaries" (keep)
- Remove any hemp/CBD related business names

#### 2. Cross-Reference Validation
**Placer vs Regulator Matching**:
- Address-based matching (primary)
- Coordinate-based matching (FL - need to geocode regulator data)
- Business name fuzzy matching
- Gap analysis and coverage reporting

#### 3. Dispensary Age Analysis
**PA Advantage**: Opening dates available in regulator data
**Strategy**:
- Flag dispensaries open <1 year
- Analyze impact on model performance
- Consider separate modeling for new vs established

## Expected Dataset Outcomes

### After Processing:
- **FL Training Data**: ~650-700 cannabis dispensaries (post-filtering)
- **PA Training Data**: ~189 dispensaries
- **Total Training**: ~850-900 dispensaries
- **Complete Competitor Lists**: 950+ dispensaries for radius analysis

### Data Quality Expectations:
- ✅ 100% visit data coverage (Placer subset)
- ✅ 100% coordinate coverage (Placer subset)
- ✅ Complete competitive landscape (regulator data)
- ✅ Validation benchmarks (18 Insa stores)

## Next Steps Priority

1. **Hemp/CBD Filtering**: Clean FL Placer data first
2. **Cross-Reference Engine**: Build Placer vs Regulator matching
3. **Coordinate Integration**: Geocode regulator addresses where needed
4. **Age Analysis**: Implement >1 year flagging using PA opening dates
5. **Census Integration**: Pull demographics for all ~900 locations

This is an excellent foundation for the enhanced multi-state model with significantly more data than the original PA model's ~150 dispensaries!

---
**Status**: Ready to begin processing tool development based on actual data characteristics.