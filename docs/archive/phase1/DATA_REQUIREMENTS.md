# Multi-State Dispensary Model - Data Requirements

**Status**: Planning Phase - Awaiting Daniel's Fresh Datasets
**Last Updated**: October 22, 2025

## Overview

This document outlines the data requirements for the enhanced multi-state dispensary prediction model covering Pennsylvania and Florida. All datasets will be provided by Daniel as fresh, current data.

## Core Data Requirements

### 1. Placer Data (Primary Training Data)
**Source**: Daniel to provide fresh Placer extracts
**Coverage**: Pennsylvania & Florida dispensaries
**Time Period**: Previous 12 months
**Required Fields**:
- Dispensary name and address
- Coordinates (latitude, longitude)
- Estimated annual visits
- Square footage
- Visits per square foot
- Any available operational dates

**Quality Standards**:
- Current/active dispensaries only
- Verified coordinate accuracy
- Visit data validation against business logic
- Cross-reference with state regulator lists

### 2. State Regulator Data (Competitive Landscape)
**Source**: Daniel to provide official state lists
**Purpose**: Complete competitive analysis + Placer data validation

#### Pennsylvania Department of Health
- Complete list of licensed dispensaries
- License types (Medical vs Adult-Use)
- Addresses and entity names
- License status and dates

#### Florida Department of Health / Office of Medical Marijuana Use
- Complete list of licensed dispensaries
- License types and operational status
- Addresses and entity names
- Opening dates where available

**Integration Strategy**:
- **Full regulator lists** for competitor counting
- **Placer subset** for visit-based training features
- Cross-reference to identify data gaps and validate accuracy

### 3. Census Demographics (Feature Engineering)
**Source**: US Census Bureau (to be pulled programmatically)
**Granularity**: Census tract level
**Coverage**: Pennsylvania & Florida

**Required Demographics**:
- Total population by tract
- Age distribution (key age groups for cannabis consumers)
- Household income distribution
- Per capita income
- Education levels (high school, college+)
- Population density metrics

### 4. Insa Performance Data (Validation Benchmark)
**Source**: Daniel to provide actual Insa store performance
**Purpose**: Model validation and calibration

**Required Fields**:
- Store addresses and coordinates
- Opening dates
- License types (Medical vs Adult-Use)
- Actual monthly/annual visit counts
- Market performance context

**States**: Florida (primary), Massachusetts, Connecticut (additional validation)

### 5. Traffic/Accessibility Data (Enhanced Features)
**Source**: State DOT data (where available)
**Coverage**: Pennsylvania (PennDOT), Florida (FDOT if accessible)

**Preferred Fields**:
- AADT (Annual Average Daily Traffic) counts
- Road classification and accessibility
- Proximity to major thoroughfares

## Data Processing Architecture

### Dual-Dataset Strategy
Based on your guidance, we'll implement a sophisticated approach:

1. **Complete Competitive Landscape**: Use full state regulator lists to count all competitors in radius analysis
2. **Training Features**: Use Placer data subset for visit-based predictions and performance modeling
3. **Validation Layer**: Cross-reference between regulator and Placer lists to identify data quality issues

### Dispensary Age Analysis
- Flag dispensaries open <1 year using regulator opening dates
- Analyze whether to include/exclude new dispensaries in training
- Consider separate modeling approaches for established vs new locations

### Data Quality Standards
- **Manual Review Required**: Daniel to review all datasets before processing
- **Real Data Only**: Zero synthetic estimates or approximations
- **Source Documentation**: Complete provenance tracking for all datasets
- **Validation Pipeline**: Multi-layer verification against multiple sources

## Data Preparation Workflow

### Phase 1: Dataset Review and Planning
1. Daniel provides fresh Placer data for PA & FL
2. Daniel provides current state regulator lists
3. Joint review of data quality and coverage
4. Finalize processing approach based on actual data characteristics

### Phase 2: Data Integration and Validation
1. Cross-reference Placer data against regulator lists
2. Identify and document any gaps or discrepancies
3. Pull census demographics for relevant areas
4. Integrate Insa performance data for validation

### Phase 3: Feature Engineering Pipeline
1. Multi-radius population analysis (1mi, 3mi, 5mi, 10mi)
2. Distance-weighted competition metrics using full regulator lists
3. Demographic profiling and market saturation indicators
4. State-specific factors and accessibility metrics

## Expected Dataset Sizes

Based on your estimates:
- **Florida**: ~600 dispensaries in Placer data
- **Pennsylvania**: ~150 dispensaries in Placer data
- **Total Training Dataset**: ~750 dispensaries (significant improvement over PA model's ~150)

## Next Steps

**Awaiting from Daniel**:
1. Fresh Placer data extracts (PA & FL)
2. Current state regulator dispensary lists (PA & FL)
3. Insa performance data for validation

**Ready to Build**:
- Data processing pipeline architecture
- Cross-reference and validation tools
- Census demographics integration
- Feature engineering framework

Once datasets are provided, we can proceed with building the processing tools and integration pipeline while maintaining the highest data quality standards.

---

**Note**: No data collection or processing will begin until Daniel provides and approves all source datasets.