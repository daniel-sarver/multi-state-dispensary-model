"""
Model Training Module for Multi-State Dispensary Prediction

This module trains and validates the multi-state dispensary prediction model using:
1. Ridge regression with hyperparameter tuning
2. 5-fold stratified cross-validation
3. Leave-one-state-out validation
4. State-specific performance analysis
5. Feature importance analysis

Author: Multi-State Dispensary Model Team
Date: October 2025
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.model_selection import cross_val_score, cross_validate, KFold, StratifiedKFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from prepare_training_data import DataPreparator


class MultiStateModelTrainer:
    """
    Trains and validates multi-state dispensary prediction model.

    Uses Ridge regression with state interactions and comprehensive validation.
    """

    def __init__(self, model_version='v2'):
        """
        Initialize ModelTrainer.

        Parameters:
        -----------
        model_version : str
            Model version identifier (default: 'v2' for corrected data)
        """
        self.model_version = model_version
        self.preparator = None
        self.prepared_data = None
        self.model = None
        self.best_alpha = None
        self.cv_scores = {}
        self.state_scores = {}
        self.training_report = {}

    def prepare_data(self):
        """
        Prepare training data using DataPreparator.

        Returns:
        --------
        dict
            Prepared data dictionary
        """
        print("="*60)
        print(f"STEP 1: DATA PREPARATION (Model {self.model_version})")
        print("="*60 + "\n")

        # Use corrected dataset and target for model v2
        if self.model_version == 'v2':
            data_path = 'data/processed/combined_with_competitive_features_corrected.csv'
            target_column = 'corrected_visits'
            print(f"Model v2: Using corrected dataset and target '{target_column}' (ANNUAL visits)\n")
        else:
            data_path = 'data/processed/combined_with_competitive_features.csv'
            target_column = 'visits'
            print(f"Model v1: Using uncorrected dataset and target '{target_column}'\n")

        self.preparator = DataPreparator(
            data_path=data_path,
            target_column=target_column
        )
        self.prepared_data = self.preparator.prepare_data(
            test_size=0.2,
            random_state=42,
            scale=True
        )

        # Save preparation report with version
        report_path = f'data/models/data_preparation_report_{self.model_version}.json'
        self.preparator.save_report(report_path)

        return self.prepared_data

    def train_ridge_regression(self, alphas=None):
        """
        Train Ridge regression with Pipeline for proper cross-validation.

        Uses Pipeline([('scaler', StandardScaler()), ('ridge', Ridge())])
        to prevent data leakage during cross-validation.

        Parameters:
        -----------
        alphas : list, optional
            List of alpha values to try (default: [0.01, 0.1, 1, 10, 100, 1000])

        Returns:
        --------
        Pipeline
            Trained Pipeline with StandardScaler and Ridge regression
        """
        print("\n" + "="*60)
        print("STEP 2: RIDGE REGRESSION WITH PIPELINE (PROPER CV)")
        print("="*60 + "\n")

        if alphas is None:
            alphas = [0.01, 0.1, 1, 10, 100, 1000]

        X_train = self.prepared_data['X_train']  # Unscaled
        y_train = self.prepared_data['y_train']

        print(f"Training Ridge regression with {len(alphas)} alpha values: {alphas}")
        print("Using Pipeline with StandardScaler for proper cross-validation...")

        # Create Pipeline to avoid data leakage in CV
        # Scaler will be fitted separately on each CV fold
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge())
        ])

        # Test each alpha via CV
        best_alpha = None
        best_score = -np.inf

        for alpha in alphas:
            pipeline.set_params(ridge__alpha=alpha)
            scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='r2')
            mean_score = scores.mean()
            if mean_score > best_score:
                best_score = mean_score
                best_alpha = alpha

        self.best_alpha = best_alpha
        print(f"\nBest alpha selected: {self.best_alpha} (CV R² = {best_score:.4f})")

        # Train final pipeline with best alpha on full training set
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=self.best_alpha))
        ])
        self.model.fit(X_train, y_train)

        # Calculate training set performance
        train_pred = self.model.predict(X_train)
        train_r2 = r2_score(y_train, train_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        train_mae = mean_absolute_error(y_train, train_pred)

        print(f"\nTraining set performance (alpha={self.best_alpha}):")
        print(f"  R² = {train_r2:.4f}")
        print(f"  RMSE = {train_rmse:.2f} visits")
        print(f"  MAE = {train_mae:.2f} visits")

        self.training_report['ridge_regression'] = {
            'best_alpha': float(self.best_alpha),
            'train_r2': float(train_r2),
            'train_rmse': float(train_rmse),
            'train_mae': float(train_mae),
            'training_samples': len(X_train),
            'features': len(X_train.columns),
            'uses_pipeline': True,
            'cv_method': 'Proper Pipeline with StandardScaler'
        }

        return self.model

    def cross_validate_model(self, cv_folds=5):
        """
        Perform k-fold cross-validation.

        Parameters:
        -----------
        cv_folds : int
            Number of folds for cross-validation (default: 5)

        Returns:
        --------
        dict
            Cross-validation scores
        """
        print("\n" + "="*60)
        print("STEP 3: 5-FOLD CROSS-VALIDATION")
        print("="*60 + "\n")

        X_train = self.prepared_data['X_train']
        y_train = self.prepared_data['y_train']

        # Create regular k-fold (not stratified, since target is continuous)
        kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)

        print(f"Performing {cv_folds}-fold cross-validation...")

        # Perform cross-validation with multiple metrics
        cv_results = cross_validate(
            self.model,
            X_train,
            y_train,
            cv=kf,
            scoring={
                'r2': 'r2',
                'neg_rmse': 'neg_root_mean_squared_error',
                'neg_mae': 'neg_mean_absolute_error'
            },
            return_train_score=True
        )

        # Calculate mean and std for each metric
        cv_r2_mean = cv_results['test_r2'].mean()
        cv_r2_std = cv_results['test_r2'].std()
        cv_rmse_mean = -cv_results['test_neg_rmse'].mean()
        cv_rmse_std = cv_results['test_neg_rmse'].std()
        cv_mae_mean = -cv_results['test_neg_mae'].mean()
        cv_mae_std = cv_results['test_neg_mae'].std()

        print(f"\n{cv_folds}-Fold Cross-Validation Results:")
        print(f"  R² = {cv_r2_mean:.4f} ± {cv_r2_std:.4f}")
        print(f"  RMSE = {cv_rmse_mean:.2f} ± {cv_rmse_std:.2f} visits")
        print(f"  MAE = {cv_mae_mean:.2f} ± {cv_mae_std:.2f} visits")

        # Check if target R² achieved
        target_r2 = 0.15
        if cv_r2_mean >= target_r2:
            print(f"\n✅ TARGET ACHIEVED: R² = {cv_r2_mean:.4f} >= {target_r2}")
        else:
            print(f"\n⚠️  Target not achieved: R² = {cv_r2_mean:.4f} < {target_r2}")
            print("   Consider trying ensemble methods (Random Forest, XGBoost)")

        self.cv_scores = {
            'r2_mean': float(cv_r2_mean),
            'r2_std': float(cv_r2_std),
            'rmse_mean': float(cv_rmse_mean),
            'rmse_std': float(cv_rmse_std),
            'mae_mean': float(cv_mae_mean),
            'mae_std': float(cv_mae_std),
            'cv_folds': cv_folds,
            'target_achieved': bool(cv_r2_mean >= target_r2)
        }

        self.training_report['cross_validation'] = self.cv_scores

        return self.cv_scores

    def evaluate_test_set(self):
        """
        Evaluate model on held-out test set.

        Returns:
        --------
        dict
            Test set performance metrics
        """
        print("\n" + "="*60)
        print("STEP 4: TEST SET EVALUATION")
        print("="*60 + "\n")

        X_test = self.prepared_data['X_test']
        y_test = self.prepared_data['y_test']

        # Make predictions
        y_pred = self.model.predict(X_test)

        # Calculate metrics
        test_r2 = r2_score(y_test, y_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        test_mae = mean_absolute_error(y_test, y_pred)

        # Calculate MAPE (handle division by zero)
        test_mape = mean_absolute_percentage_error(y_test, y_pred) * 100

        print(f"Test Set Performance:")
        print(f"  R² = {test_r2:.4f}")
        print(f"  RMSE = {test_rmse:.2f} visits")
        print(f"  MAE = {test_mae:.2f} visits")
        print(f"  MAPE = {test_mape:.2f}%")

        test_scores = {
            'r2': float(test_r2),
            'rmse': float(test_rmse),
            'mae': float(test_mae),
            'mape': float(test_mape),
            'test_samples': len(X_test)
        }

        self.training_report['test_set'] = test_scores

        return test_scores

    def evaluate_state_performance(self):
        """
        Evaluate model performance separately for FL and PA.

        Returns:
        --------
        dict
            State-specific performance metrics
        """
        print("\n" + "="*60)
        print("STEP 5: STATE-SPECIFIC PERFORMANCE ANALYSIS")
        print("="*60 + "\n")

        X_test = self.prepared_data['X_test']
        y_test = self.prepared_data['y_test']

        # Make predictions
        y_pred = self.model.predict(X_test)

        # Get original state labels from training_df (safer than relying on scaled features)
        training_df = self.prepared_data['training_df']
        test_states = training_df.loc[X_test.index, 'state']

        fl_mask = test_states == 'FL'
        pa_mask = test_states == 'PA'

        # Florida metrics
        fl_r2 = r2_score(y_test[fl_mask], y_pred[fl_mask])
        fl_rmse = np.sqrt(mean_squared_error(y_test[fl_mask], y_pred[fl_mask]))
        fl_mae = mean_absolute_error(y_test[fl_mask], y_pred[fl_mask])

        # Pennsylvania metrics
        pa_r2 = r2_score(y_test[pa_mask], y_pred[pa_mask])
        pa_rmse = np.sqrt(mean_squared_error(y_test[pa_mask], y_pred[pa_mask]))
        pa_mae = mean_absolute_error(y_test[pa_mask], y_pred[pa_mask])

        print(f"Florida Performance (n={fl_mask.sum()}):")
        print(f"  R² = {fl_r2:.4f}")
        print(f"  RMSE = {fl_rmse:.2f} visits")
        print(f"  MAE = {fl_mae:.2f} visits")

        print(f"\nPennsylvania Performance (n={pa_mask.sum()}):")
        print(f"  R² = {pa_r2:.4f}")
        print(f"  RMSE = {pa_rmse:.2f} visits")
        print(f"  MAE = {pa_mae:.2f} visits")

        # Check state difference
        r2_diff = abs(fl_r2 - pa_r2)
        if r2_diff > 0.10:
            print(f"\n⚠️  Large state difference: ΔR² = {r2_diff:.4f}")
            print("   Consider training separate FL and PA models")
        else:
            print(f"\n✅ State performance similar: ΔR² = {r2_diff:.4f}")
            print("   Unified model is appropriate")

        self.state_scores = {
            'florida': {
                'r2': float(fl_r2),
                'rmse': float(fl_rmse),
                'mae': float(fl_mae),
                'n_samples': int(fl_mask.sum())
            },
            'pennsylvania': {
                'r2': float(pa_r2),
                'rmse': float(pa_rmse),
                'mae': float(pa_mae),
                'n_samples': int(pa_mask.sum())
            },
            'r2_difference': float(r2_diff),
            'unified_appropriate': bool(r2_diff <= 0.10)
        }

        self.training_report['state_performance'] = self.state_scores

        return self.state_scores

    def leave_one_state_out_validation(self):
        """
        Perform leave-one-state-out cross-validation.

        Tests generalization across states.

        Returns:
        --------
        dict
            Leave-one-state-out validation scores
        """
        print("\n" + "="*60)
        print("STEP 6: LEAVE-ONE-STATE-OUT VALIDATION")
        print("="*60 + "\n")

        X_train = self.prepared_data['X_train']
        y_train = self.prepared_data['y_train']

        # Get original state labels from training_df
        training_df = self.prepared_data['training_df']
        train_states = training_df.loc[X_train.index, 'state']

        # Train on FL, test on PA
        print("Training on FL, testing on PA...")
        fl_train_mask = train_states == 'FL'
        pa_train_mask = train_states == 'PA'

        X_fl = X_train[fl_train_mask]
        y_fl = y_train[fl_train_mask]
        X_pa = X_train[pa_train_mask]
        y_pa = y_train[pa_train_mask]

        # Train FL-only model with Pipeline
        model_fl = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=self.best_alpha))
        ])
        model_fl.fit(X_fl, y_fl)
        pa_pred = model_fl.predict(X_pa)
        fl_to_pa_r2 = r2_score(y_pa, pa_pred)

        print(f"  FL → PA: R² = {fl_to_pa_r2:.4f}")

        # Train on PA, test on FL
        print("Training on PA, testing on FL...")
        model_pa = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=self.best_alpha))
        ])
        model_pa.fit(X_pa, y_pa)
        fl_pred = model_pa.predict(X_fl)
        pa_to_fl_r2 = r2_score(y_fl, fl_pred)

        print(f"  PA → FL: R² = {pa_to_fl_r2:.4f}")

        # Average cross-state generalization
        avg_r2 = (fl_to_pa_r2 + pa_to_fl_r2) / 2
        print(f"\nAverage cross-state R²: {avg_r2:.4f}")

        if avg_r2 > 0.05:
            print("✅ Model generalizes across states")
        else:
            print("⚠️  Poor cross-state generalization")

        loso_scores = {
            'fl_to_pa_r2': float(fl_to_pa_r2),
            'pa_to_fl_r2': float(pa_to_fl_r2),
            'average_r2': float(avg_r2),
            'generalizes': bool(avg_r2 > 0.05)
        }

        self.training_report['leave_one_state_out'] = loso_scores

        return loso_scores

    def analyze_feature_importance(self, top_n=20):
        """
        Analyze feature importance from Ridge coefficients.

        Extracts coefficients from the Ridge model inside the Pipeline.

        Parameters:
        -----------
        top_n : int
            Number of top features to display (default: 20)

        Returns:
        --------
        pd.DataFrame
            Feature importance DataFrame
        """
        print("\n" + "="*60)
        print("STEP 7: FEATURE IMPORTANCE ANALYSIS")
        print("="*60 + "\n")

        feature_names = self.prepared_data['feature_names']
        # Extract coefficients from the Ridge model inside the Pipeline
        coefficients = self.model.named_steps['ridge'].coef_

        # Create DataFrame
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'coefficient': coefficients,
            'abs_coefficient': np.abs(coefficients)
        })

        # Sort by absolute coefficient
        feature_importance = feature_importance.sort_values('abs_coefficient', ascending=False)

        print(f"Top {top_n} Most Important Features:")
        print("="*60)
        print(feature_importance.head(top_n).to_string(index=False))

        # Save to file
        output_path = Path('data/models/feature_importance.csv')
        feature_importance.to_csv(output_path, index=False)
        print(f"\nFull feature importance saved to: {output_path}")

        # Store in report
        self.training_report['feature_importance'] = {
            'top_10': feature_importance.head(10)[['feature', 'coefficient']].to_dict('records')
        }

        return feature_importance

    def generate_residual_plots(self):
        """
        Generate residual diagnostic plots.
        """
        print("\n" + "="*60)
        print("STEP 8: RESIDUAL ANALYSIS PLOTS")
        print("="*60 + "\n")

        X_test = self.prepared_data['X_test']
        y_test = self.prepared_data['y_test']
        y_pred = self.model.predict(X_test)

        residuals = y_test - y_pred

        # Create figure with 4 subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # 1. Actual vs Predicted
        axes[0, 0].scatter(y_test, y_pred, alpha=0.6, edgecolors='k', linewidth=0.5)
        axes[0, 0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        axes[0, 0].set_xlabel('Actual Visits')
        axes[0, 0].set_ylabel('Predicted Visits')
        axes[0, 0].set_title('Actual vs Predicted Visits')
        axes[0, 0].grid(True, alpha=0.3)

        # 2. Residuals vs Predicted
        axes[0, 1].scatter(y_pred, residuals, alpha=0.6, edgecolors='k', linewidth=0.5)
        axes[0, 1].axhline(y=0, color='r', linestyle='--', lw=2)
        axes[0, 1].set_xlabel('Predicted Visits')
        axes[0, 1].set_ylabel('Residuals')
        axes[0, 1].set_title('Residual Plot')
        axes[0, 1].grid(True, alpha=0.3)

        # 3. Histogram of Residuals
        axes[1, 0].hist(residuals, bins=30, edgecolor='black', alpha=0.7)
        axes[1, 0].set_xlabel('Residuals')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Distribution of Residuals')
        axes[1, 0].axvline(x=0, color='r', linestyle='--', lw=2)
        axes[1, 0].grid(True, alpha=0.3)

        # 4. Q-Q Plot
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1, 1])
        axes[1, 1].set_title('Q-Q Plot')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        output_path = Path('data/models/validation_plots/residual_analysis.png')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Residual plots saved to: {output_path}")

        plt.close()

    def save_model(self, model_path=None):
        """
        Save trained model to pickle file.

        Parameters:
        -----------
        model_path : str, optional
            Path to save model (default: auto-generated based on model_version)
        """
        print("\n" + "="*60)
        print("STEP 9: SAVING MODEL ARTIFACT")
        print("="*60 + "\n")

        # Auto-generate path if not provided
        if model_path is None:
            model_path = f'data/models/multi_state_model_{self.model_version}.pkl'

        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # Create model package
        model_package = {
            'model': self.model,
            'scaler': self.prepared_data['scaler'],
            'feature_names': self.prepared_data['feature_names'],
            'best_alpha': self.best_alpha,
            'training_date': datetime.now().isoformat(),
            'model_version': self.model_version,
            'target_column': self.preparator.target_column,
            'data_units': 'annual_visits',  # Important: predictions are in annual visits
            'training_report': self.training_report
        }

        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(model_package, f)

        print(f"Model saved to: {model_path}")
        print(f"Model version: {self.model_version}")
        print(f"Target: {self.preparator.target_column} (ANNUAL visits)")
        print(f"Model size: {model_path.stat().st_size / 1024:.2f} KB")

        return model_path

    def save_training_report(self, report_path=None):
        """
        Save comprehensive training report to JSON.

        Parameters:
        -----------
        report_path : str, optional
            Path to save report (default: auto-generated based on model_version)
        """
        # Auto-generate path if not provided
        if report_path is None:
            report_path = f'data/models/multi_state_model_{self.model_version}_training_report.json'

        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata
        self.training_report['metadata'] = {
            'training_date': datetime.now().isoformat(),
            'model_type': 'Ridge Regression',
            'baseline_r2': 0.0716,
            'target_r2': 0.15,
            'improvement_factor': float(self.cv_scores['r2_mean'] / 0.0716) if self.cv_scores else None
        }

        # Save report
        with open(report_path, 'w') as f:
            json.dump(self.training_report, f, indent=2)

        print(f"\nTraining report saved to: {report_path}")

        return report_path

    def train_and_evaluate(self):
        """
        Execute complete training and evaluation pipeline.

        Returns:
        --------
        dict
            Complete training report
        """
        print("\n" + "="*60)
        print("MULTI-STATE DISPENSARY MODEL - TRAINING PIPELINE")
        print("="*60 + "\n")

        # Step 1: Prepare data
        self.prepare_data()

        # Step 2: Train Ridge regression
        self.train_ridge_regression()

        # Step 3: Cross-validation
        self.cross_validate_model()

        # Step 4: Test set evaluation
        self.evaluate_test_set()

        # Step 5: State-specific performance
        self.evaluate_state_performance()

        # Step 6: Leave-one-state-out validation
        self.leave_one_state_out_validation()

        # Step 7: Feature importance
        self.analyze_feature_importance()

        # Step 8: Residual plots
        self.generate_residual_plots()

        # Step 9: Save model
        self.save_model()

        # Step 10: Save training report
        self.save_training_report()

        # Print summary
        print("\n" + "="*60)
        print("TRAINING COMPLETE - SUMMARY")
        print("="*60)
        print(f"\nCross-Validation R²: {self.cv_scores['r2_mean']:.4f} ± {self.cv_scores['r2_std']:.4f}")
        print(f"Test Set R²: {self.training_report['test_set']['r2']:.4f}")
        print(f"Florida R²: {self.state_scores['florida']['r2']:.4f}")
        print(f"Pennsylvania R²: {self.state_scores['pennsylvania']['r2']:.4f}")
        print(f"\nImprovement over baseline (0.0716): {self.cv_scores['r2_mean'] / 0.0716:.2f}x")
        print(f"Target R² (0.15) achieved: {self.cv_scores['target_achieved']}")
        print("="*60 + "\n")

        return self.training_report


if __name__ == '__main__':
    # Train model v2 with corrected data
    print("Training Multi-State Dispensary Model v2")
    print("Using corrected dataset with calibrated annual visits\n")

    trainer = MultiStateModelTrainer(model_version='v2')
    training_report = trainer.train_and_evaluate()

    print("\nModel v2 training and evaluation completed successfully!")
    print("Predictions are in ANNUAL visits (corrected, calibrated to Insa actual)")
