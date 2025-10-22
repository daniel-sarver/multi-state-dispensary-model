# Processed Data Directory

This directory contains cleaned, validated, and integrated datasets ready for analysis.

## Data Processing Pipeline

### Integration Files
- `multi_state_dispensaries.csv` - Combined PA & FL dispensary dataset
- `census_demographics_integrated.csv` - Merged census data for both states
- `competition_analysis.csv` - Complete competitive landscape data
- `insa_validation_data.csv` - Actual performance data for validation

### Feature Engineering Files
- `population_features.csv` - Multi-radius population analysis
- `competition_features.csv` - Distance-weighted competition metrics
- `demographic_features.csv` - Age, income, education profiles
- `traffic_features.csv` - AADT and accessibility metrics
- `state_features.csv` - State-specific factors and multipliers

### Final Training Data
- `training_dataset.csv` - Complete feature set for model training
- `validation_dataset.csv` - Hold-out data for final validation
- `feature_definitions.json` - Documentation of all features

## Data Quality Standards

- **Validation Passed**: All files validated for completeness and accuracy
- **Feature Documentation**: All columns documented with source and calculation method
- **Coordinate Validation**: All coordinates verified within state boundaries
- **Missing Data Handling**: Explicit strategy for handling any missing values

## File Naming Convention

- Use descriptive names with snake_case
- Include processing date in filename for versioned files
- Document any transformations applied in accompanying .txt files