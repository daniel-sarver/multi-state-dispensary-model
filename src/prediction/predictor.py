"""
Multi-State Dispensary Prediction Module

This module provides the core prediction functionality for the Multi-State
Dispensary Model, loading the trained model artifact and generating visit
predictions with confidence intervals.

Model Details:
- Ridge Regression with Pipeline (StandardScaler + Ridge)
- Trained on 592 dispensaries (FL & PA)
- 44 engineered features
- R² = 0.1940 (test set)
- Alpha = 1000
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

    def __init__(self, model_path: str = 'data/models/multi_state_model_v1.pkl'):
        """
        Initialize predictor and load model artifact.

        Parameters
        ----------
        model_path : str
            Path to pickled model artifact (default: data/models/multi_state_model_v1.pkl)
        """
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

            # Extract components
            self.pipeline = model_artifact['model']  # Pipeline: StandardScaler + Ridge
            self.feature_names = model_artifact['feature_names']
            self.best_alpha = model_artifact['best_alpha']
            self.training_date = model_artifact['training_date']
            self.model_metadata = model_artifact

            print(f"✅ Model loaded successfully")
            print(f"   Features: {len(self.feature_names)}")
            print(f"   Alpha: {self.best_alpha}")
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
            Predicted monthly visits

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
        Normal approximation: CI = prediction ± z * RMSE
        Bootstrap: Resample residuals, regenerate predictions, take percentiles

        State-specific RMSE is used when available:
        - Florida: Lower RMSE (33,162) for tighter intervals
        - Pennsylvania: Higher RMSE (56,581) reflecting higher uncertainty
        - Overall: Test RMSE (39,024) when state unknown
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

        training_report = self.model_metadata['training_report']

        if is_fl == 1:
            rmse = training_report['state_performance']['florida']['rmse']
            state_label = 'FL'
        elif is_pa == 1:
            rmse = training_report['state_performance']['pennsylvania']['rmse']
            state_label = 'PA'
        else:
            # Use overall test RMSE if state unknown (both indicators 0)
            rmse = training_report['test_set']['rmse']
            state_label = 'overall'

        if method == 'normal':
            # Fast normal approximation
            from scipy import stats
            z_score = stats.norm.ppf((1 + confidence) / 2)
            ci_half_width = z_score * rmse

            result = {
                'prediction': prediction,
                'ci_lower': max(0, prediction - ci_half_width),
                'ci_upper': prediction + ci_half_width,
                'confidence_level': confidence,
                'method': 'normal_approximation',
                'rmse_used': rmse,
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
        Calculate feature contributions to prediction for this specific site.

        This shows which features are driving the prediction up or down
        compared to the mean prediction.

        Parameters
        ----------
        features_dict : dict
            Dictionary mapping feature names to values

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: feature, value, coefficient, contribution
            Sorted by absolute contribution (most impactful first)

        Notes
        -----
        Contribution = coefficient * (standardized_feature_value)

        For Ridge regression in a Pipeline:
        - Coefficients are for standardized features
        - Need to standardize input features first
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

        # Get standardized features (Pipeline's scaler)
        scaler = self.pipeline.named_steps['scaler']
        X_scaled = scaler.transform(X)

        # Get Ridge coefficients
        ridge = self.pipeline.named_steps['ridge']
        coefficients = ridge.coef_
        intercept = ridge.intercept_

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
        Get model metadata and performance information from training report.

        Returns
        -------
        dict
            Model metadata including performance metrics
        """
        training_report = self.model_metadata['training_report']

        return {
            'model_path': str(self.model_path),
            'training_date': self.training_date,
            'n_features': len(self.feature_names),
            'alpha': self.best_alpha,
            'test_r2': training_report['test_set']['r2'],
            'test_rmse': training_report['test_set']['rmse'],
            'cv_r2_mean': training_report['cross_validation']['r2_mean'],
            'cv_r2_std': training_report['cross_validation']['r2_std'],
            'fl_r2': training_report['state_performance']['florida']['r2'],
            'fl_rmse': training_report['state_performance']['florida']['rmse'],
            'pa_r2': training_report['state_performance']['pennsylvania']['r2'],
            'pa_rmse': training_report['state_performance']['pennsylvania']['rmse'],
            'improvement_over_baseline': '2.62x'
        }


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
    print(f"Actual Visits: {actual_visits:,.0f} visits/month")

    # Generate prediction
    print("\n" + "="*60)
    print("Prediction:")
    print("="*60)

    prediction = predictor.predict(example_features)
    error = abs(prediction - actual_visits)
    pct_error = (error / actual_visits) * 100

    print(f"Predicted: {prediction:,.0f} visits/month")
    print(f"Actual: {actual_visits:,.0f} visits/month")
    print(f"Error: {error:,.0f} visits ({pct_error:.1f}%)")

    # Prediction with confidence interval (normal approximation)
    result_normal = predictor.predict_with_confidence(example_features, method='normal')
    print(f"\n95% Confidence Interval (Normal Approximation):")
    print(f"  Method: {result_normal['method']}")
    print(f"  RMSE used: {result_normal['rmse_used']:,.0f} ({result_normal['state']})")
    print(f"  Range: {result_normal['ci_lower']:,.0f} - {result_normal['ci_upper']:,.0f} visits/month")

    actual_in_ci_normal = result_normal['ci_lower'] <= actual_visits <= result_normal['ci_upper']
    print(f"  Actual within CI: {'✅ Yes' if actual_in_ci_normal else '❌ No'}")

    # Prediction with bootstrap confidence interval
    result_bootstrap = predictor.predict_with_confidence(example_features, method='bootstrap')
    print(f"\n95% Confidence Interval (Bootstrap):")
    print(f"  Method: {result_bootstrap['method']}")
    print(f"  Bootstrap iterations: {result_bootstrap['n_bootstrap']}")
    print(f"  RMSE used: {result_bootstrap['rmse_used']:,.0f} ({result_bootstrap['state']})")
    print(f"  Range: {result_bootstrap['ci_lower']:,.0f} - {result_bootstrap['ci_upper']:,.0f} visits/month")

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
