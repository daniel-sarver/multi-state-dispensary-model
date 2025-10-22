# Data Processing Pipeline Architecture

**Status**: Planning Phase - Architecture Ready for Daniel's Datasets
**Last Updated**: October 22, 2025

## Overview

This document outlines the data processing pipeline architecture for the multi-state dispensary model. The pipeline is designed to handle fresh datasets provided by Daniel while maintaining the highest quality standards.

## Pipeline Architecture

### Stage 1: Data Ingestion and Validation
**Input**: Daniel's fresh datasets
**Output**: Validated, standardized datasets ready for integration

#### 1.1 Placer Data Processing
```
Raw Placer Data (PA & FL)
    ↓
Coordinate Validation (state boundaries)
    ↓
Visit Data Cleaning and Validation
    ↓
Business Logic Validation
    ↓
Standardized Placer Dataset
```

#### 1.2 State Regulator Data Processing
```
Raw Regulator Lists (PA DOH + FL DOH/OMMU)
    ↓
Address Standardization
    ↓
License Status Validation
    ↓
Opening Date Analysis (>1 year flagging)
    ↓
Standardized Regulator Dataset
```

#### 1.3 Cross-Reference Validation
```
Placer Dataset + Regulator Dataset
    ↓
Address-Based Matching
    ↓
Coordinate-Based Matching
    ↓
Business Name Fuzzy Matching
    ↓
Gap Analysis and Quality Report
```

### Stage 2: Competitive Landscape Integration
**Purpose**: Implement dual-dataset strategy

#### 2.1 Complete Competitor Mapping
- Use **full regulator lists** for competitor counting
- Multi-radius analysis (1mi, 3mi, 5mi, 10mi)
- Distance-weighted competitor metrics
- Market saturation calculations

#### 2.2 Training Dataset Preparation
- Use **Placer subset** for visit-based features
- Exclude dispensaries with data quality issues
- Flag new dispensaries (<1 year) for separate analysis

### Stage 3: Census Demographics Integration
**Source**: US Census Bureau API (automated pull)

#### 3.1 Geographic Matching
```
Dispensary Coordinates
    ↓
Census Tract Identification
    ↓
Multi-Radius Population Analysis
    ↓
Demographic Feature Engineering
```

#### 3.2 Demographic Features
- Population density by radius
- Age distribution analysis
- Income and education profiles
- Market opportunity indicators

### Stage 4: Enhanced Feature Engineering
**Output**: Complete feature matrix for model training

#### 4.1 Population Features
- Multi-radius population (1mi, 3mi, 5mi, 10mi)
- Distance-weighted population density
- Demographic segmentation scores

#### 4.2 Competition Features
- Competitor count by radius (using full regulator lists)
- Distance-weighted competition intensity
- Market saturation ratios
- Closest competitor analysis

#### 4.3 State-Specific Features
- Pennsylvania vs Florida market indicators
- Medical vs Adult-Use program maturity
- Regulatory environment factors

#### 4.4 Accessibility Features
- Traffic data integration (where available)
- Urban vs suburban classification
- Economic indicators by region

### Stage 5: Validation Data Integration
**Purpose**: Insa performance benchmarking

#### 5.1 Insa Data Processing
```
Actual Insa Performance Data
    ↓
Coordinate Matching with Training Data
    ↓
Performance Validation Metrics
    ↓
Model Calibration Benchmarks
```

## Quality Assurance Framework

### Data Validation Checkpoints
1. **Coordinate Validation**: All coordinates within state boundaries
2. **Business Logic Validation**: Visit counts reasonable for dispensary size
3. **Cross-Reference Validation**: Placer vs regulator list consistency
4. **Temporal Validation**: Opening dates logical and consistent
5. **Completeness Validation**: Required fields populated

### Error Handling Strategy
- **Graceful Degradation**: Handle missing data without breaking pipeline
- **Quality Scoring**: Assign confidence scores to all matches
- **Manual Review Flags**: Identify records requiring Daniel's review
- **Audit Trail**: Complete processing history and decision documentation

## Processing Tools Architecture

### Tool 1: Data Ingestion and Validation
**File**: `src/data_integration/ingest_and_validate.py`
**Purpose**: Process Daniel's raw datasets with comprehensive validation

**Features**:
- Multi-format data reading (CSV, Excel, JSON)
- Coordinate boundary validation
- Business logic checks
- Quality scoring and reporting

### Tool 2: Cross-Reference Engine
**File**: `src/data_integration/cross_reference_engine.py`
**Purpose**: Match Placer data with regulator lists

**Features**:
- Multiple matching strategies (address, coordinates, business name)
- Fuzzy string matching for name variations
- Confidence scoring for all matches
- Gap analysis and quality reporting

### Tool 3: Census Demographics Processor
**File**: `src/feature_engineering/census_demographics.py`
**Purpose**: Automated census data collection and integration

**Features**:
- Census tract identification from coordinates
- Multi-radius demographic analysis
- Feature engineering pipeline
- Demographic profiling tools

### Tool 4: Feature Engineering Pipeline
**File**: `src/feature_engineering/multi_state_features.py`
**Purpose**: Complete feature matrix generation

**Features**:
- Population and competition analysis
- State-specific feature generation
- Distance-weighted calculations
- Market saturation metrics

### Tool 5: Validation Framework
**File**: `src/validation/insa_benchmarking.py`
**Purpose**: Model validation against actual performance

**Features**:
- Insa data integration
- Performance comparison metrics
- Model calibration tools
- Validation reporting

## Data Flow Diagram

```
Daniel's Raw Datasets
    ↓
[Stage 1] Ingestion & Validation
    ↓
[Stage 2] Cross-Reference & Integration
    ↓
[Stage 3] Census Demographics Addition
    ↓
[Stage 4] Feature Engineering
    ↓
[Stage 5] Validation Data Integration
    ↓
Complete Training Dataset
    ↓
Model Development Pipeline
```

## Output Standards

### Primary Outputs
- `multi_state_training_dataset.csv`: Complete feature matrix
- `regulator_competitive_landscape.csv`: Full competitor lists
- `data_quality_report.json`: Comprehensive quality metrics
- `feature_definitions.json`: Documentation of all features

### Quality Reports
- Cross-reference match report
- Data completeness analysis
- Coordinate validation summary
- Business logic validation results

## Security and Data Handling

### Data Protection
- No raw datasets stored in Git repository
- Processed datasets in `.gitignore`
- Local processing only (no cloud data transfer)
- Complete audit trail of all transformations

### Reproducibility
- Deterministic processing pipeline
- Version control of all processing scripts
- Complete parameter documentation
- Processing history logging

## Ready State

The architecture is complete and ready to process Daniel's datasets. All tools will be built to handle the specific characteristics of the provided data while maintaining:

- **Data Integrity**: Real data only, no synthetic estimates
- **Quality Standards**: Comprehensive validation at every step
- **Flexibility**: Adaptable to actual dataset characteristics
- **Transparency**: Complete documentation and audit trails

**Next Step**: Awaiting Daniel's fresh datasets to begin building the specific processing tools.