# Models Directory

This directory contains trained model artifacts, configurations, and performance metrics.

## Model Files

### Trained Models
- `multi_state_ridge_model.pkl` - Production Ridge regression model
- `ensemble_model.pkl` - Enhanced ensemble model (if developed)
- `state_scalers.pkl` - Feature scaling transformers

### Model Configurations
- `model_config.json` - Hyperparameters and training settings
- `feature_config.json` - Feature selection and engineering parameters
- `state_multipliers.json` - State-specific adjustment factors

### Performance Metrics
- `model_performance.json` - Cross-validation results and metrics
- `validation_results.json` - Performance on hold-out datasets
- `confidence_analysis.json` - Uncertainty quantification parameters

### Model Documentation
- `model_methodology.md` - Detailed explanation of modeling approach
- `feature_importance.json` - Analysis of feature contributions
- `validation_report.md` - Complete validation methodology and results

## Model Versioning

Models are versioned using semantic versioning (v1.0, v1.1, etc.)
- Major version: Significant architecture changes
- Minor version: Feature additions or improvements
- Each version includes complete documentation and performance comparison

## Production Model Standards

- **Cross-Validation**: All models validated using geographic cross-validation
- **Performance Baseline**: Must exceed PA model baseline (R² = 0.0716)
- **Business Validation**: Results validated against Insa actual performance
- **Uncertainty Quantification**: Confidence intervals provided for all predictions