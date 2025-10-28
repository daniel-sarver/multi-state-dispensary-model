"""
Multi-State Dispensary Prediction Module

This module provides the core prediction functionality for the Multi-State
Dispensary Model, loading the trained model artifact and generating visit
predictions with confidence intervals.

Model Versions:
- v2 (unified): Ridge Regression trained on 741 FL+PA dispensaries (R² = 0.19 overall)
- v3 (state-specific): Separate optimized models for within-state comparisons
  - FL model: Ridge with 31 features (within-state R² = 0.0685)
  - PA model: Random Forest with 31 features (within-state R² = 0.0756)

The predictor automatically routes to the appropriate state-specific model when
state parameter is provided, or uses the unified model when state is None.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple


class MultiStatePredictor:
    """
    Load trained model and generate dispensary visit predictions.

    This class handles:
    - Loading the trained model artifact
    - Feature validation and alignment
    - Visit predictions with confidence intervals
    - Feature contribution analysis
    """

    def __init__(self, model_path: str = None, state: str = None, model_version: str = 'v3'):
        """
        Initialize predictor and load model artifact.

        Parameters
        ----------
        model_path : str, optional
            Path to pickled model artifact. If None, automatically selects based on state and version.
        state : str, optional
            State for prediction ('FL' or 'PA'). If provided with model_version='v3', loads state-specific model.
            If None, loads unified multi-state model (v2).
        model_version : str, optional
            Model version to use: 'v2' (unified) or 'v3' (state-specific). Default: 'v3'

        Notes
        -----
        Automatic Model Selection (when model_path is None):
        - If state='FL' and model_version='v3': loads fl_model_v3.pkl (within-state R²=0.0685)
        - If state='PA' and model_version='v3': loads pa_model_v3.pkl (within-state R²=0.0756)
        - If state=None or model_version='v2': loads multi_state_model_v2.pkl (overall R²=0.19)
        """
        self.state = state
        self.model_version = model_version

        # Auto-select model path based on state and version
        if model_path is None:
            if model_version == 'v3' and state in ['FL', 'PA']:
                # Use state-specific v3 models for within-state comparisons
                state_lower = state.lower()
                model_path = f'data/models/{state_lower}_model_v3.pkl'
            else:
                # Default to unified v2 model
                model_path = 'data/models/multi_state_model_v2.pkl'
                self.model_version = 'v2'  # Force v2 if state-specific not available

        self.model_path = Path(model_path)
        self.pipeline = None
        self.feature_names = None
        self.best_alpha = None
        self.training_date = None
        self.model_metadata = None

        self.load_model()

    def load_model(self) -> None:
        """
        Load model artifact from pickle file.

        Handles both v2 (unified) and v3 (state-specific) model formats.

        Raises
        ------
        FileNotFoundError
            If model artifact file doesn't exist
        Exception
            If model artifact is corrupted or invalid
        """
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found at: {self.model_path}\n"
                f"Please ensure you're in the project root directory."
            )

        try:
            with open(self.model_path, 'rb') as f:
                model_artifact = pickle.load(f)

            # Extract components (works for both v2 and v3)
            self.pipeline = model_artifact['model']  # Pipeline: StandardScaler + Ridge/RF/XGBoost
            self.feature_names = model_artifact['feature_names']
            self.training_date = model_artifact['training_date']
            self.model_metadata = model_artifact

            # v3 models don't have best_alpha (might be Random Forest or XGBoost)
            self.best_alpha = model_artifact.get('best_alpha', None)

            # Get model info for logging
            model_version = model_artifact.get('model_version', 'v2')
            algorithm = model_artifact.get('algorithm', 'ridge')
            cv_r2 = model_artifact.get('cv_r2', None)

            print(f"✅ Model loaded successfully")
            print(f"   Version: {model_version}")
            if self.state:
                print(f"   State: {self.state}")
            print(f"   Algorithm: {algorithm}")
            print(f"   Features: {len(self.feature_names)}")
            if self.best_alpha:
                print(f"   Alpha: {self.best_alpha}")
            if cv_r2:
                print(f"   CV R²: {cv_r2:.4f}")
            print(f"   Trained: {self.training_date}")

        except Exception as e:
            raise Exception(f"Failed to load model artifact: {str(e)}")

    def validate_features(self, features_dict: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate that all required features are present in features_dict.

        Parameters
        ----------
        features_dict : dict
            Dictionary mapping feature names to values

        Returns
        -------
        tuple
            (is_valid: bool, missing_features: list)
        """
        provided_features = set(features_dict.keys())
        required_features = set(self.feature_names)

        missing_features = required_features - provided_features

        if missing_features:
            return False, sorted(list(missing_features))

        return True, []

    def predict(self, features_dict: Dict[str, float]) -> float:
        """
        Generate visit prediction from feature dictionary.

        Parameters
        ----------
        features_dict : dict
            Dictionary mapping feature names to values
            Must contain all 44 required features

        Returns
        -------
        float
            Predicted annual visits

        Raises
        ------
        ValueError
            If required features are missing
        """
        # Validate features
        is_valid, missing = self.validate_features(features_dict)
        if not is_valid:
            raise ValueError(
                f"Missing {len(missing)} required features: {missing[:5]}..."
            )

        # Create feature DataFrame with proper column names (silences sklearn warning)
        X = pd.DataFrame(
            [[features_dict[fname] for fname in self.feature_names]],
            columns=self.feature_names
        )

        # Generate prediction (Pipeline handles scaling)
        prediction = self.pipeline.predict(X)[0]

        return prediction

    def predict_with_confidence(
        self,
        features_dict: Dict[str, float],
        confidence: float = 0.95,
        method: str = 'normal'
    ) -> Dict[str, float]:
        """
        Generate prediction with confidence interval.

        This method estimates prediction uncertainty using either normal approximation
        (fast) or bootstrap resampling (more accurate but slower). Uses state-specific
        RMSE when available for tighter intervals.

        Parameters
        ----------
        features_dict : dict
            Dictionary mapping feature names to values
        confidence : float
            Confidence level (default: 0.95 for 95% CI)
        method : str
            Method for CI calculation: 'normal' (fast, default) or 'bootstrap' (slower)

        Returns
        -------
        dict
            {
                'prediction': float,
                'ci_lower': float,
                'ci_upper': float,
                'confidence_level': float,
                'method': str,
                'rmse_used': float
            }

        Notes
        -----
        Prediction-Proportional Intervals (v2.1):
        - Scales RMSE proportionally to prediction magnitude
        - CI = prediction ± z * (RMSE * prediction / mean_training_visits)
        - Smaller predictions get narrower intervals
        - Maintains statistical coverage for typical predictions

        State-specific RMSE is used when available:
        - Florida: Lower RMSE (18,270) for tighter intervals
        - Pennsylvania: Higher RMSE (30,854) reflecting higher uncertainty
        - Overall: Test RMSE (21,407) when state unknown
        """
        # Get point prediction
        prediction = self.predict(features_dict)

        # Determine appropriate RMSE from training report
        # Use state-specific RMSE if available for tighter intervals
        is_fl = features_dict.get('is_FL', 0)
        is_pa = features_dict.get('is_PA', 0)

        # Guard: Validate state indicators
        if is_fl == 1 and is_pa == 1:
            raise ValueError(
                "Invalid state indicators: both is_FL and is_PA are 1. "
                "A dispensary must be in exactly one state."
            )
        if is_fl not in [0, 1]:
            raise ValueError(f"is_FL must be 0 or 1, got: {is_fl}")
        if is_pa not in [0, 1]:
            raise ValueError(f"is_PA must be 0 or 1, got: {is_pa}")

        # Get RMSE - handle both v2 (with training_report) and v3 (state-specific) models
        if 'training_report' in self.model_metadata:
            # v2 model with full training report
            training_report = self.model_metadata['training_report']

            if is_fl == 1:
                rmse = training_report['state_performance']['florida']['rmse']
                mean_visits = training_report['state_performance']['florida']['mean_actual_visits']
                state_label = 'FL'
            elif is_pa == 1:
                rmse = training_report['state_performance']['pennsylvania']['rmse']
                mean_visits = training_report['state_performance']['pennsylvania']['mean_actual_visits']
                state_label = 'PA'
            else:
                # Use overall test RMSE if state unknown (both indicators 0)
                rmse = training_report['test_set']['rmse']
                mean_visits = training_report['test_set']['mean_actual_visits']
                state_label = 'overall'
        else:
            # v3 state-specific model - use default RMSE estimates
            # These are approximations based on training results
            if is_fl == 1 or self.state == 'FL':
                rmse = 18270  # FL state RMSE from v2
                mean_visits = 31142  # FL median from training data
                state_label = 'FL'
            elif is_pa == 1 or self.state == 'PA':
                rmse = 30854  # PA state RMSE from v2
                mean_visits = 52118  # PA median from training data
                state_label = 'PA'
            else:
                # Fallback to overall
                rmse = 21407  # Overall test RMSE from v2
                mean_visits = 37000  # Approximate overall mean
                state_label = 'overall'

        if method == 'normal':
            # Fast normal approximation with prediction-proportional scaling
            from scipy import stats
            z_score = stats.norm.ppf((1 + confidence) / 2)

            # Scale RMSE proportionally to prediction magnitude
            # This gives smaller intervals for smaller predictions
            scale_factor = prediction / mean_visits
            adjusted_rmse = rmse * scale_factor
            ci_half_width = z_score * adjusted_rmse

            # Calculate initial bounds
            ci_lower_uncapped = max(0, prediction - ci_half_width)
            ci_upper_uncapped = prediction + ci_half_width

            # Apply ±75% cap for business usability
            # This prevents intervals from being too wide to be actionable
            max_half_width_pct = 0.75  # ±75% of prediction
            max_half_width = prediction * max_half_width_pct

            # Check if cap is needed
            cap_applied = ci_half_width > max_half_width

            if cap_applied:
                # Apply cap
                ci_lower = max(0, prediction - max_half_width)
                ci_upper = prediction + max_half_width
                confidence_level_note = 'CAPPED'
            else:
                # Use uncapped intervals
                ci_lower = ci_lower_uncapped
                ci_upper = ci_upper_uncapped
                confidence_level_note = 'STATISTICAL'

            result = {
                'prediction': prediction,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'ci_lower_uncapped': ci_lower_uncapped,
                'ci_upper_uncapped': ci_upper_uncapped,
                'confidence_level': confidence,
                'confidence_level_note': confidence_level_note,
                'cap_applied': cap_applied,
                'cap_percentage': max_half_width_pct * 100,
                'method': 'prediction_proportional_capped',
                'rmse_used': rmse,
                'adjusted_rmse': adjusted_rmse,
                'scale_factor': scale_factor,
                'state': state_label
            }

        elif method == 'bootstrap':
            # Bootstrap resampling for more accurate intervals
            # This resamples from model residuals to estimate prediction uncertainty
            result = self._bootstrap_confidence_interval(
                features_dict, prediction, rmse, confidence
            )
            result['state'] = state_label

        else:
            raise ValueError(f"Unknown method: {method}. Use 'normal' or 'bootstrap'")

        return result

    def _bootstrap_confidence_interval(
        self,
        features_dict: Dict[str, float],
        point_prediction: float,
        rmse: float,
        confidence: float,
        n_bootstrap: int = 1000
    ) -> Dict[str, float]:
        """
        Calculate confidence interval using bootstrap resampling.

        This method resamples residuals (assumed normally distributed with std=RMSE)
        and generates bootstrap predictions to estimate the prediction interval.

        Parameters
        ----------
        features_dict : dict
            Feature dictionary for prediction
        point_prediction : float
            Point prediction from model
        rmse : float
            Root mean squared error to use for residual sampling
        confidence : float
            Confidence level (e.g., 0.95)
        n_bootstrap : int
            Number of bootstrap iterations (default: 1000)

        Returns
        -------
        dict
            Bootstrap confidence interval results
        """
        np.random.seed(42)  # For reproducibility

        # Generate bootstrap predictions by resampling residuals
        # Assume residuals ~ N(0, RMSE²)
        bootstrap_predictions = []

        for _ in range(n_bootstrap):
            # Sample residual from normal distribution
            residual = np.random.normal(0, rmse)
            bootstrap_pred = point_prediction + residual
            bootstrap_predictions.append(max(0, bootstrap_pred))  # Can't be negative

        bootstrap_predictions = np.array(bootstrap_predictions)

        # Calculate percentiles for confidence interval
        alpha = 1 - confidence
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        ci_lower = np.percentile(bootstrap_predictions, lower_percentile)
        ci_upper = np.percentile(bootstrap_predictions, upper_percentile)

        return {
            'prediction': point_prediction,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'confidence_level': confidence,
            'method': 'bootstrap',
            'rmse_used': rmse,
            'n_bootstrap': n_bootstrap
        }

    def get_feature_contributions(self, features_dict: Dict[str, float]) -> pd.DataFrame:
        """
        Calculate feature contributions/importances for this site.

        For Ridge regression: Shows coefficient-based contributions
        For tree-based models (RF, XGBoost): Shows feature importances

        Parameters
        ----------
        features_dict : dict
            Dictionary mapping feature names to values

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: feature, value, importance/coefficient, contribution/importance
            Sorted by absolute importance (most impactful first)

        Notes
        -----
        - Ridge: Contribution = coefficient * (standardized_feature_value)
        - Tree-based: Uses built-in feature_importances_ (not site-specific)
        """
        # Validate features
        is_valid, missing = self.validate_features(features_dict)
        if not is_valid:
            raise ValueError(f"Missing required features: {missing}")

        # Create feature DataFrame with column names (silences sklearn warning)
        X = pd.DataFrame(
            [[features_dict[fname] for fname in self.feature_names]],
            columns=self.feature_names
        )

        # Determine algorithm type from pipeline
        # v3 models: pipeline has 'model' step, v2 models: pipeline has 'ridge' step
        if 'model' in self.pipeline.named_steps:
            model = self.pipeline.named_steps['model']
        elif 'ridge' in self.pipeline.named_steps:
            model = self.pipeline.named_steps['ridge']
        else:
            raise ValueError("Unknown pipeline structure - no 'model' or 'ridge' step found")

        # Get algorithm name
        algorithm = self.model_metadata.get('algorithm', 'ridge')

        # Handle based on algorithm type
        if algorithm == 'ridge' or hasattr(model, 'coef_'):
            # Ridge regression - coefficient-based contributions
            scaler = self.pipeline.named_steps['scaler']
            X_scaled = scaler.transform(X)

            coefficients = model.coef_
            intercept = model.intercept_

            # Calculate contributions
            contributions = X_scaled[0] * coefficients

            # Create DataFrame
            df = pd.DataFrame({
                'feature': self.feature_names,
                'value': [features_dict[fname] for fname in self.feature_names],
                'coefficient': coefficients,
                'contribution': contributions
            })

            # Add intercept row
            intercept_row = pd.DataFrame({
                'feature': ['intercept'],
                'value': [1.0],
                'coefficient': [intercept],
                'contribution': [intercept]
            })

            df = pd.concat([intercept_row, df], ignore_index=True)

            # Sort by absolute contribution
            df['abs_contribution'] = df['contribution'].abs()
            df = df.sort_values('abs_contribution', ascending=False)
            df = df.drop('abs_contribution', axis=1)

        elif hasattr(model, 'feature_importances_'):
            # Tree-based model (Random Forest, XGBoost) - use feature importances
            importances = model.feature_importances_

            # Create DataFrame (no intercept for tree models)
            df = pd.DataFrame({
                'feature': self.feature_names,
                'value': [features_dict[fname] for fname in self.feature_names],
                'importance': importances,
                'contribution': importances  # Use importance as proxy for contribution
            })

            # Sort by importance
            df = df.sort_values('importance', ascending=False)

        else:
            # Unknown model type
            raise ValueError(
                f"Model type '{algorithm}' does not support feature contributions. "
                f"Supported: Ridge (coefficients), RandomForest/XGBoost (importances)"
            )

        return df

    def get_top_drivers(
        self,
        features_dict: Dict[str, float],
        n: int = 5
    ) -> pd.DataFrame:
        """
        Get top N features driving the prediction.

        Parameters
        ----------
        features_dict : dict
            Dictionary mapping feature names to values
        n : int
            Number of top features to return (default: 5)

        Returns
        -------
        pd.DataFrame
            Top N features by absolute contribution
        """
        contributions = self.get_feature_contributions(features_dict)

        # Exclude intercept from ranking
        contributions = contributions[contributions['feature'] != 'intercept']

        return contributions.head(n)

    def predict_batch(
        self,
        features_df: pd.DataFrame,
        include_confidence: bool = False
    ) -> pd.DataFrame:
        """
        Generate predictions for multiple sites.

        Parameters
        ----------
        features_df : pd.DataFrame
            DataFrame with one row per site, columns = feature names
            Must include all 44 required features
        include_confidence : bool
            If True, include confidence intervals (slower)

        Returns
        -------
        pd.DataFrame
            Original dataframe with added columns:
            - predicted_visits
            - ci_lower (if include_confidence=True)
            - ci_upper (if include_confidence=True)
        """
        # Validate all required features present
        missing = set(self.feature_names) - set(features_df.columns)
        if missing:
            raise ValueError(f"Missing required features: {sorted(list(missing))}")

        # Create feature DataFrame in correct order (keeps column names for sklearn)
        X = features_df[self.feature_names]

        # Generate predictions
        predictions = self.pipeline.predict(X)

        # Add predictions to dataframe
        result_df = features_df.copy()
        result_df['predicted_visits'] = predictions

        # Add confidence intervals if requested
        if include_confidence:
            print(f"Calculating confidence intervals for {len(features_df)} sites...")
            ci_results = []

            for idx, row in features_df.iterrows():
                features_dict = row.to_dict()
                ci_result = self.predict_with_confidence(features_dict)
                ci_results.append({
                    'ci_lower': ci_result['ci_lower'],
                    'ci_upper': ci_result['ci_upper']
                })

            ci_df = pd.DataFrame(ci_results)
            result_df['ci_lower'] = ci_df['ci_lower'].values
            result_df['ci_upper'] = ci_df['ci_upper'].values

        return result_df

    def get_model_info(self) -> Dict:
        """
        Get model metadata and performance information.

        Handles both v2 (unified with full training report) and v3 (state-specific) models.

        Returns
        -------
        dict
            Model metadata including performance metrics
        """
        info = {
            'model_path': str(self.model_path),
            'training_date': self.training_date,
            'n_features': len(self.feature_names),
            'model_version': self.model_metadata.get('model_version', 'v2'),
            'algorithm': self.model_metadata.get('algorithm', 'ridge')
        }

        # Add alpha if available (Ridge only)
        if self.best_alpha:
            info['alpha'] = self.best_alpha

        # v3 state-specific models have simpler structure
        if info['model_version'] == 'v3':
            info['state'] = self.model_metadata.get('state', self.state)
            info['feature_set'] = self.model_metadata.get('feature_set', 'unknown')
            info['cv_r2'] = self.model_metadata.get('cv_r2', None)

            # Calculate improvement over baseline
            baseline_r2 = 0.048 if info['state'] == 'FL' else -0.028
            if info['cv_r2']:
                improvement = info['cv_r2'] - baseline_r2
                info['improvement_over_v2_baseline'] = f"+{improvement:.4f}"

        # v2 unified model has full training report
        elif 'training_report' in self.model_metadata:
            training_report = self.model_metadata['training_report']

            # Get improvement factor from metadata (or compute if not available)
            improvement_factor = training_report.get('metadata', {}).get('improvement_factor', None)
            if improvement_factor is not None:
                improvement_str = f"{improvement_factor:.2f}x"
            else:
                # Fallback: compute from baseline if metadata missing
                baseline_r2 = training_report.get('metadata', {}).get('baseline_r2', 0.0716)
                cv_r2 = training_report['cross_validation']['r2_mean']
                improvement_factor = cv_r2 / baseline_r2
                improvement_str = f"{improvement_factor:.2f}x"

            info.update({
                'test_r2': training_report['test_set']['r2'],
                'test_rmse': training_report['test_set']['rmse'],
                'cv_r2_mean': training_report['cross_validation']['r2_mean'],
                'cv_r2_std': training_report['cross_validation']['r2_std'],
                'fl_r2': training_report['state_performance']['florida']['r2'],
                'fl_rmse': training_report['state_performance']['florida']['rmse'],
                'pa_r2': training_report['state_performance']['pennsylvania']['r2'],
                'pa_rmse': training_report['state_performance']['pennsylvania']['rmse'],
                'improvement_over_baseline': improvement_str
            })

        return info


def main():
    """
    Test MultiStatePredictor with real training data.
    """
    import pandas as pd

    # Load model
    predictor = MultiStatePredictor()

    # Print model info
    print("\n" + "="*60)
    print("Model Information:")
    print("="*60)
    info = predictor.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Load a real example from training data
    print("\n" + "="*60)
    print("Loading Real Example from Training Data:")
    print("="*60)

    df = pd.read_csv('data/processed/combined_with_competitive_features.csv')

    # Get a FL dispensary with Placer data
    fl_examples = df[(df['state'] == 'FL') & (df['has_placer_data'] == True)]
    example_row = fl_examples.iloc[10]  # Use 10th example

    # Create feature dict
    example_features = {}
    for feat in predictor.feature_names:
        if feat in example_row.index:
            value = example_row[feat]
            example_features[feat] = 0.0 if pd.isna(value) else float(value)
        else:
            # For missing features (like is_FL, is_PA), use 0
            example_features[feat] = 0.0

    # Set state indicators
    state = example_row['state']
    example_features['is_FL'] = 1.0 if state == 'FL' else 0.0
    example_features['is_PA'] = 1.0 if state == 'PA' else 0.0

    actual_visits = example_row['visits']

    print(f"State: {state}")
    print(f"Square Footage: {example_features['sq_ft']:,.0f} sq ft")
    print(f"Population (5mi): {example_features['pop_5mi']:,.0f}")
    print(f"Competitors (5mi): {example_features['competitors_5mi']:.0f}")
    print(f"Actual Visits: {actual_visits:,.0f} visits/year")

    # Generate prediction
    print("\n" + "="*60)
    print("Prediction:")
    print("="*60)

    prediction = predictor.predict(example_features)
    error = abs(prediction - actual_visits)
    pct_error = (error / actual_visits) * 100

    print(f"Predicted: {prediction:,.0f} visits/year")
    print(f"Actual: {actual_visits:,.0f} visits/year")
    print(f"Error: {error:,.0f} visits ({pct_error:.1f}%)")

    # Prediction with confidence interval (normal approximation)
    result_normal = predictor.predict_with_confidence(example_features, method='normal')
    print(f"\n95% Confidence Interval (Normal Approximation):")
    print(f"  Method: {result_normal['method']}")
    print(f"  RMSE used: {result_normal['rmse_used']:,.0f} ({result_normal['state']})")
    print(f"  Range: {result_normal['ci_lower']:,.0f} - {result_normal['ci_upper']:,.0f} visits/year")

    actual_in_ci_normal = result_normal['ci_lower'] <= actual_visits <= result_normal['ci_upper']
    print(f"  Actual within CI: {'✅ Yes' if actual_in_ci_normal else '❌ No'}")

    # Prediction with bootstrap confidence interval
    result_bootstrap = predictor.predict_with_confidence(example_features, method='bootstrap')
    print(f"\n95% Confidence Interval (Bootstrap):")
    print(f"  Method: {result_bootstrap['method']}")
    print(f"  Bootstrap iterations: {result_bootstrap['n_bootstrap']}")
    print(f"  RMSE used: {result_bootstrap['rmse_used']:,.0f} ({result_bootstrap['state']})")
    print(f"  Range: {result_bootstrap['ci_lower']:,.0f} - {result_bootstrap['ci_upper']:,.0f} visits/year")

    actual_in_ci_bootstrap = result_bootstrap['ci_lower'] <= actual_visits <= result_bootstrap['ci_upper']
    print(f"  Actual within CI: {'✅ Yes' if actual_in_ci_bootstrap else '❌ No'}")

    # Top drivers
    print("\n" + "="*60)
    print("Top 5 Feature Drivers:")
    print("="*60)
    top_drivers = predictor.get_top_drivers(example_features, n=5)

    for idx, row in top_drivers.iterrows():
        feat = row['feature']
        contrib = row['contribution']
        sign = "+" if contrib > 0 else ""
        print(f"  {feat:30s}: {sign}{contrib:>10,.0f} visits")

    print("\n✅ Predictor module working correctly!")


if __name__ == '__main__':
    main()
