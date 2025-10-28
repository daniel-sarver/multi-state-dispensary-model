"""
State-Specific Model Training for Within-State Predictions

This module trains separate FL-only and PA-only models to optimize
within-state predictive power. Tests 5 feature combinations per state
with 3 algorithms each (Ridge, Random Forest, XGBoost).

Context:
- Model v2 overall R²=0.19 is inflated by between-state differences
- Within-state R²: FL=0.048, PA=-0.028 (very weak)
- User needs to compare sites WITHIN states, not across states
- Goal: Empirically test if separate models + feature selection improve within-state predictions

Author: Multi-State Dispensary Model Team
Date: October 28, 2025
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import pickle
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class StateSpecificModelTrainer:
    """
    Trains state-specific models with comprehensive feature selection testing.

    For each state (FL and PA):
    1. Tests 5 feature combinations (full, competition-focused, demographics, best-of-both, minimal)
    2. Tests 3 algorithms per combination (Ridge, Random Forest, XGBoost)
    3. Evaluates within-state R² via 5-fold cross-validation
    4. Selects best model for deployment
    """

    def __init__(self, data_path='data/processed/combined_with_competitive_features_corrected.csv'):
        """
        Initialize trainer.

        Parameters:
        -----------
        data_path : str
            Path to corrected training data
        """
        self.data_path = data_path
        self.df = None
        self.fl_data = None
        self.pa_data = None
        self.results = {
            'florida': {},
            'pennsylvania': {},
            'metadata': {}
        }

    def load_and_split_data(self):
        """
        Load data and split by state.

        Returns:
        --------
        tuple
            (fl_df, pa_df)
        """
        print("="*80)
        print("LOADING AND SPLITTING DATA BY STATE")
        print("="*80 + "\n")

        self.df = pd.read_csv(self.data_path)

        # Filter to training data only (has_placer_data == True)
        training_df = self.df[self.df['has_placer_data'] == True].copy()

        # Split by state
        self.fl_data = training_df[training_df['state'] == 'FL'].copy()
        self.pa_data = training_df[training_df['state'] == 'PA'].copy()

        print(f"Total training dispensaries: {len(training_df)}")
        print(f"  Florida: {len(self.fl_data)} dispensaries")
        print(f"  Pennsylvania: {len(self.pa_data)} dispensaries\n")

        # Store in metadata
        self.results['metadata']['total_training'] = len(training_df)
        self.results['metadata']['florida_training'] = len(self.fl_data)
        self.results['metadata']['pennsylvania_training'] = len(self.pa_data)

        return self.fl_data, self.pa_data

    def get_florida_feature_sets(self):
        """
        Define 5 feature combinations for Florida.

        Florida patterns: Local competition (1mi, 3mi, 5mi) + demographics

        Returns:
        --------
        dict
            Feature set name -> list of feature names
        """
        # Base features (always included)
        base = ['sq_ft']

        # Competition features by radius
        comp_short = ['competitors_1mi', 'competitors_3mi', 'competitors_5mi',
                      'saturation_1mi', 'saturation_3mi', 'saturation_5mi']
        comp_medium = ['competitors_10mi', 'saturation_10mi']
        comp_long = ['competitors_20mi', 'saturation_20mi', 'competition_weighted_20mi']

        # Demographics features
        demographics = [
            'pop_1mi', 'pop_3mi', 'pop_5mi', 'pop_10mi', 'pop_20mi',
            'population_density', 'total_population',
            'median_household_income', 'per_capita_income',
            'pct_bachelor_plus', 'bachelors_degree', 'masters_degree', 'doctorate_degree', 'professional_degree',
            'median_age', 'total_pop_25_plus',
            'affluent_market_5mi', 'educated_urban_score', 'age_adjusted_catchment_3mi'
        ]

        # State indicator
        state_indicators = ['is_FL', 'is_PA']

        # Feature sets
        feature_sets = {
            'full_model': None,  # Will use all available features

            'competition_focused': base + comp_short + comp_medium + comp_long + state_indicators,

            'demographics_focused': base + demographics + state_indicators,

            'best_of_both': base + comp_short + [
                'pop_1mi', 'pop_3mi', 'pop_5mi',
                'educated_urban_score', 'affluent_market_5mi',
                'pct_bachelor_plus', 'median_household_income'
            ] + state_indicators,

            'minimal': ['sq_ft', 'competitors_5mi', 'pop_5mi'] + state_indicators
        }

        return feature_sets

    def get_pennsylvania_feature_sets(self):
        """
        Define 5 feature combinations for Pennsylvania.

        Pennsylvania patterns: Regional competition (10mi, 20mi) + demographics

        Returns:
        --------
        dict
            Feature set name -> list of feature names
        """
        # Base features (always included)
        base = ['sq_ft']

        # Competition features by radius
        comp_short = ['competitors_1mi', 'competitors_3mi', 'competitors_5mi']
        comp_regional = ['competitors_10mi', 'competitors_20mi',
                        'saturation_10mi', 'saturation_20mi',
                        'competition_weighted_20mi']

        # Demographics features
        demographics = [
            'pop_1mi', 'pop_3mi', 'pop_5mi', 'pop_10mi', 'pop_20mi',
            'population_density', 'total_population',
            'median_household_income', 'per_capita_income',
            'pct_bachelor_plus', 'bachelors_degree', 'masters_degree', 'doctorate_degree', 'professional_degree',
            'median_age', 'total_pop_25_plus',
            'affluent_market_5mi', 'educated_urban_score', 'age_adjusted_catchment_3mi'
        ]

        # State indicator
        state_indicators = ['is_FL', 'is_PA']

        # Feature sets
        feature_sets = {
            'full_model': None,  # Will use all available features

            'competition_focused': base + comp_regional + state_indicators,

            'demographics_focused': base + demographics + state_indicators,

            'best_of_both': base + comp_regional + [
                'pop_10mi', 'pop_20mi',
                'pct_bachelor_plus', 'affluent_market_5mi',
                'median_household_income', 'per_capita_income'
            ] + state_indicators,

            'minimal': ['sq_ft', 'competitors_20mi', 'pop_20mi'] + state_indicators
        }

        return feature_sets

    def prepare_features(self, df, feature_list=None):
        """
        Prepare feature matrix and target variable.

        Parameters:
        -----------
        df : pd.DataFrame
            State-specific data
        feature_list : list, optional
            List of features to use (if None, use all available)

        Returns:
        --------
        tuple
            (X, y, feature_names)
        """
        # Exclude non-feature columns
        exclude_patterns = [
            'regulator_', 'placer_', 'census_geoid', 'census_tract_name',
            'census_state_fips', 'census_county_fips', 'census_tract_fips',
            'has_placer_data', 'census_data_complete', 'census_api_error',
            'match_score', 'match_type', 'match_details', 'data_source',
            'chain_name', 'chain_id', 'dispensary_id',
            'latitude', 'longitude', 'address',
            'visits_per_sq_ft',  # UNCORRECTED derived variable
            'corrected_visits_per_sq_ft',  # Derived target variable (DATA LEAKAGE!)
            'corrected_visits_step1',  # Intermediate correction step (DATA LEAKAGE!)
            'visits',  # UNCORRECTED target
            'state',  # We use is_FL/is_PA instead
            'tract_area_sqm', 'census_tract_fips', 'census_tract_name', 'census_county_fips', 'census_geoid',
            'match_score', 'match_type', 'match_details', 'census_state_fips',
            'correction_placer_factor', 'maturity_factor', 'months_operational_at_collection'
        ]

        # Get target
        y = df['corrected_visits'].copy()

        # Get features
        if feature_list is None:
            # Use all available features
            feature_cols = [col for col in df.columns
                          if col != 'corrected_visits'
                          and not any(col.startswith(pattern) or col == pattern.rstrip('_')
                                    for pattern in exclude_patterns)]
        else:
            # Use specified features (that exist in data)
            feature_cols = [col for col in feature_list if col in df.columns]

        X = df[feature_cols].copy()

        # Filter to numeric columns only (exclude strings, dates, etc.)
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        X = X[numeric_cols].copy()

        # Handle missing values with median imputation
        # Drop columns that are entirely NaN
        cols_to_drop = []
        for col in X.columns:
            if X[col].isnull().all():
                cols_to_drop.append(col)
            elif X[col].isnull().any():
                median_val = X[col].median()
                X[col].fillna(median_val, inplace=True)

        if cols_to_drop:
            X = X.drop(columns=cols_to_drop)
            numeric_cols = [c for c in numeric_cols if c not in cols_to_drop]

        return X, y, numeric_cols

    def test_algorithm(self, X, y, algorithm_name, **kwargs):
        """
        Test a specific algorithm with 5-fold cross-validation.

        Parameters:
        -----------
        X : pd.DataFrame
            Features
        y : pd.Series
            Target
        algorithm_name : str
            'ridge', 'random_forest', or 'xgboost'
        **kwargs : dict
            Algorithm-specific hyperparameters

        Returns:
        --------
        dict
            Results including mean/std R² scores
        """
        # Create pipeline with scaler
        if algorithm_name == 'ridge':
            model = Ridge(**kwargs)
        elif algorithm_name == 'random_forest':
            model = RandomForestRegressor(random_state=42, **kwargs)
        elif algorithm_name == 'xgboost':
            model = XGBRegressor(random_state=42, verbosity=0, **kwargs)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm_name}")

        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', model)
        ])

        # 5-fold cross-validation
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(pipeline, X, y, cv=kf, scoring='r2')

        # Train on full data for final model
        pipeline.fit(X, y)
        train_pred = pipeline.predict(X)
        train_r2 = r2_score(y, train_pred)
        train_rmse = np.sqrt(mean_squared_error(y, train_pred))
        train_mae = mean_absolute_error(y, train_pred)

        results = {
            'algorithm': algorithm_name,
            'cv_r2_mean': float(cv_scores.mean()),
            'cv_r2_std': float(cv_scores.std()),
            'cv_r2_scores': [float(s) for s in cv_scores],
            'train_r2': float(train_r2),
            'train_rmse': float(train_rmse),
            'train_mae': float(train_mae),
            'hyperparameters': kwargs,
            'pipeline': pipeline  # Save for potential use
        }

        return results

    def train_state_models(self, state_name, state_df, feature_sets):
        """
        Train all feature combinations and algorithms for a state.

        Parameters:
        -----------
        state_name : str
            'florida' or 'pennsylvania'
        state_df : pd.DataFrame
            State-specific training data
        feature_sets : dict
            Feature combinations to test

        Returns:
        --------
        dict
            Results for all combinations
        """
        print("\n" + "="*80)
        print(f"TRAINING {state_name.upper()} MODELS")
        print("="*80 + "\n")

        state_results = {}
        best_r2 = -np.inf
        best_config = None

        for feature_set_name, feature_list in feature_sets.items():
            print(f"\n{'─'*80}")
            print(f"Feature Set: {feature_set_name.replace('_', ' ').title()}")
            print(f"{'─'*80}")

            # Prepare features
            X, y, feature_names = self.prepare_features(state_df, feature_list)

            print(f"Features: {len(feature_names)}")
            print(f"Samples: {len(X)}\n")

            feature_set_results = {
                'feature_count': len(feature_names),
                'feature_names': feature_names,
                'algorithms': {}
            }

            # Test Ridge Regression
            print("  Testing Ridge Regression...")
            ridge_results = self.test_algorithm(X, y, 'ridge', alpha=1000)
            feature_set_results['algorithms']['ridge'] = ridge_results
            print(f"    CV R² = {ridge_results['cv_r2_mean']:.4f} ± {ridge_results['cv_r2_std']:.4f}")

            # Check if best so far
            if ridge_results['cv_r2_mean'] > best_r2:
                best_r2 = ridge_results['cv_r2_mean']
                best_config = {
                    'feature_set': feature_set_name,
                    'algorithm': 'ridge',
                    'cv_r2': best_r2,
                    'feature_names': feature_names,
                    'pipeline': ridge_results['pipeline']
                }

            # Test Random Forest
            print("  Testing Random Forest...")
            rf_results = self.test_algorithm(X, y, 'random_forest',
                                            n_estimators=100, max_depth=10,
                                            min_samples_split=10, min_samples_leaf=5)
            feature_set_results['algorithms']['random_forest'] = rf_results
            print(f"    CV R² = {rf_results['cv_r2_mean']:.4f} ± {rf_results['cv_r2_std']:.4f}")

            # Check if best so far
            if rf_results['cv_r2_mean'] > best_r2:
                best_r2 = rf_results['cv_r2_mean']
                best_config = {
                    'feature_set': feature_set_name,
                    'algorithm': 'random_forest',
                    'cv_r2': best_r2,
                    'feature_names': feature_names,
                    'pipeline': rf_results['pipeline']
                }

            # Test XGBoost
            print("  Testing XGBoost...")
            xgb_results = self.test_algorithm(X, y, 'xgboost',
                                             n_estimators=100, max_depth=6,
                                             learning_rate=0.1, subsample=0.8)
            feature_set_results['algorithms']['xgboost'] = xgb_results
            print(f"    CV R² = {xgb_results['cv_r2_mean']:.4f} ± {xgb_results['cv_r2_std']:.4f}")

            # Check if best so far
            if xgb_results['cv_r2_mean'] > best_r2:
                best_r2 = xgb_results['cv_r2_mean']
                best_config = {
                    'feature_set': feature_set_name,
                    'algorithm': 'xgboost',
                    'cv_r2': best_r2,
                    'feature_names': feature_names,
                    'pipeline': xgb_results['pipeline']
                }

            state_results[feature_set_name] = feature_set_results

        # Print best configuration
        print("\n" + "="*80)
        print(f"BEST {state_name.upper()} CONFIGURATION")
        print("="*80)
        print(f"Feature Set: {best_config['feature_set'].replace('_', ' ').title()}")
        print(f"Algorithm: {best_config['algorithm'].replace('_', ' ').title()}")
        print(f"CV R² = {best_config['cv_r2']:.4f}")
        print(f"Features: {len(best_config['feature_names'])}")
        print("="*80 + "\n")

        return state_results, best_config

    def compare_to_baseline(self):
        """
        Compare state-specific models to baseline model v2.

        Baseline within-state R²:
        - Florida: 0.048
        - Pennsylvania: -0.028
        """
        print("\n" + "="*80)
        print("COMPARISON TO BASELINE MODEL V2")
        print("="*80 + "\n")

        baseline_fl = 0.048
        baseline_pa = -0.028

        fl_best_r2 = self.results['florida']['best_config']['cv_r2']
        pa_best_r2 = self.results['pennsylvania']['best_config']['cv_r2']

        fl_improvement = fl_best_r2 - baseline_fl
        pa_improvement = pa_best_r2 - baseline_pa

        print("Florida:")
        print(f"  Baseline (v2): R² = {baseline_fl:.4f}")
        print(f"  Best (v3):     R² = {fl_best_r2:.4f}")
        print(f"  Improvement:   ΔR² = {fl_improvement:+.4f}")
        if fl_improvement > 0:
            print(f"  ✅ {fl_improvement/baseline_fl*100:.1f}% relative improvement")
        else:
            print(f"  ⚠️  No improvement over baseline")

        print("\nPennsylvania:")
        print(f"  Baseline (v2): R² = {baseline_pa:.4f}")
        print(f"  Best (v3):     R² = {pa_best_r2:.4f}")
        print(f"  Improvement:   ΔR² = {pa_improvement:+.4f}")
        if pa_best_r2 > 0:
            print(f"  ✅ Achieved positive R² (baseline was negative)")
        else:
            print(f"  ⚠️  Still negative R²")

        # Overall assessment
        print("\n" + "─"*80)
        if fl_improvement > 0.02 and pa_best_r2 > 0.05:
            print("✅ RECOMMENDATION: Deploy state-specific models (v3)")
            print("   Significant improvement in within-state predictions")
        elif fl_improvement > 0 or pa_best_r2 > baseline_pa:
            print("⚡ RECOMMENDATION: Consider deploying state-specific models (v3)")
            print("   Modest improvement, but still limited by weak features")
        else:
            print("⚠️  RECOMMENDATION: Keep unified model (v2)")
            print("   No meaningful improvement - feature limitation confirmed")
            print("   Next steps: Pursue AADT integration or operational data collection")
        print("─"*80 + "\n")

        self.results['comparison'] = {
            'baseline_fl_r2': baseline_fl,
            'baseline_pa_r2': baseline_pa,
            'best_fl_r2': fl_best_r2,
            'best_pa_r2': pa_best_r2,
            'fl_improvement': fl_improvement,
            'pa_improvement': pa_improvement
        }

    def save_models(self):
        """
        Save best state-specific models.
        """
        print("\n" + "="*80)
        print("SAVING BEST STATE-SPECIFIC MODELS")
        print("="*80 + "\n")

        # Create output directory
        output_dir = Path('data/models')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save Florida model
        fl_config = self.results['florida']['best_config']
        fl_model_path = output_dir / 'fl_model_v3.pkl'

        fl_package = {
            'model': fl_config['pipeline'],
            'feature_names': fl_config['feature_names'],
            'feature_set': fl_config['feature_set'],
            'algorithm': fl_config['algorithm'],
            'cv_r2': fl_config['cv_r2'],
            'training_date': datetime.now().isoformat(),
            'model_version': 'v3',
            'state': 'FL',
            'target_column': 'corrected_visits',
            'data_units': 'annual_visits'
        }

        with open(fl_model_path, 'wb') as f:
            pickle.dump(fl_package, f)

        print(f"✅ Florida model saved: {fl_model_path}")
        print(f"   Feature set: {fl_config['feature_set']}")
        print(f"   Algorithm: {fl_config['algorithm']}")
        print(f"   CV R² = {fl_config['cv_r2']:.4f}")

        # Save Pennsylvania model
        pa_config = self.results['pennsylvania']['best_config']
        pa_model_path = output_dir / 'pa_model_v3.pkl'

        pa_package = {
            'model': pa_config['pipeline'],
            'feature_names': pa_config['feature_names'],
            'feature_set': pa_config['feature_set'],
            'algorithm': pa_config['algorithm'],
            'cv_r2': pa_config['cv_r2'],
            'training_date': datetime.now().isoformat(),
            'model_version': 'v3',
            'state': 'PA',
            'target_column': 'corrected_visits',
            'data_units': 'annual_visits'
        }

        with open(pa_model_path, 'wb') as f:
            pickle.dump(pa_package, f)

        print(f"\n✅ Pennsylvania model saved: {pa_model_path}")
        print(f"   Feature set: {pa_config['feature_set']}")
        print(f"   Algorithm: {pa_config['algorithm']}")
        print(f"   CV R² = {pa_config['cv_r2']:.4f}")

    def save_training_report(self):
        """
        Save comprehensive training report.
        """
        # Create output directory
        output_dir = Path('data/models')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare report (exclude pipeline objects for JSON serialization)
        report = {
            'metadata': self.results['metadata'],
            'training_date': datetime.now().isoformat(),
            'model_version': 'v3',
            'florida': {},
            'pennsylvania': {},
            'comparison': self.results['comparison']
        }

        # Florida results (exclude pipeline objects)
        for feature_set, data in self.results['florida']['results'].items():
            report['florida'][feature_set] = {
                'feature_count': data['feature_count'],
                'algorithms': {}
            }
            for algo, algo_results in data['algorithms'].items():
                report['florida'][feature_set]['algorithms'][algo] = {
                    k: v for k, v in algo_results.items() if k != 'pipeline'
                }

        report['florida']['best_config'] = {
            k: v for k, v in self.results['florida']['best_config'].items()
            if k != 'pipeline'
        }

        # Pennsylvania results (exclude pipeline objects)
        for feature_set, data in self.results['pennsylvania']['results'].items():
            report['pennsylvania'][feature_set] = {
                'feature_count': data['feature_count'],
                'algorithms': {}
            }
            for algo, algo_results in data['algorithms'].items():
                report['pennsylvania'][feature_set]['algorithms'][algo] = {
                    k: v for k, v in algo_results.items() if k != 'pipeline'
                }

        report['pennsylvania']['best_config'] = {
            k: v for k, v in self.results['pennsylvania']['best_config'].items()
            if k != 'pipeline'
        }

        # Save Florida report
        fl_report_path = output_dir / 'fl_training_report_v3.json'
        with open(fl_report_path, 'w') as f:
            json.dump({k: v for k, v in report.items() if k in ['metadata', 'training_date', 'model_version', 'florida', 'comparison']},
                     f, indent=2)

        print(f"\n✅ Florida training report saved: {fl_report_path}")

        # Save Pennsylvania report
        pa_report_path = output_dir / 'pa_training_report_v3.json'
        with open(pa_report_path, 'w') as f:
            json.dump({k: v for k, v in report.items() if k in ['metadata', 'training_date', 'model_version', 'pennsylvania', 'comparison']},
                     f, indent=2)

        print(f"✅ Pennsylvania training report saved: {pa_report_path}")

        # Save combined comparison report
        comparison_output_dir = Path('analysis_output/state_models_v3')
        comparison_output_dir.mkdir(parents=True, exist_ok=True)

        comparison_path = comparison_output_dir / 'comparison_report.txt'
        with open(comparison_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("STATE-SPECIFIC MODELS V3 - PERFORMANCE COMPARISON\n")
            f.write("="*80 + "\n\n")

            f.write("BASELINE MODEL V2 (Within-State Performance):\n")
            f.write(f"  Florida: R² = {self.results['comparison']['baseline_fl_r2']:.4f}\n")
            f.write(f"  Pennsylvania: R² = {self.results['comparison']['baseline_pa_r2']:.4f}\n\n")

            f.write("BEST STATE-SPECIFIC MODELS V3:\n\n")

            fl_config = self.results['florida']['best_config']
            f.write("Florida:\n")
            f.write(f"  Feature Set: {fl_config['feature_set'].replace('_', ' ').title()}\n")
            f.write(f"  Algorithm: {fl_config['algorithm'].replace('_', ' ').title()}\n")
            f.write(f"  CV R² = {fl_config['cv_r2']:.4f}\n")
            f.write(f"  Improvement: ΔR² = {self.results['comparison']['fl_improvement']:+.4f}\n\n")

            pa_config = self.results['pennsylvania']['best_config']
            f.write("Pennsylvania:\n")
            f.write(f"  Feature Set: {pa_config['feature_set'].replace('_', ' ').title()}\n")
            f.write(f"  Algorithm: {pa_config['algorithm'].replace('_', ' ').title()}\n")
            f.write(f"  CV R² = {pa_config['cv_r2']:.4f}\n")
            f.write(f"  Improvement: ΔR² = {self.results['comparison']['pa_improvement']:+.4f}\n\n")

            f.write("="*80 + "\n")

        print(f"✅ Comparison report saved: {comparison_path}")

    def train_and_evaluate(self):
        """
        Execute complete training pipeline for state-specific models.

        Returns:
        --------
        dict
            Complete results
        """
        print("\n" + "="*80)
        print("STATE-SPECIFIC MODEL TRAINING PIPELINE (V3)")
        print("="*80 + "\n")

        # Load and split data
        self.load_and_split_data()

        # Train Florida models
        fl_feature_sets = self.get_florida_feature_sets()
        fl_results, fl_best = self.train_state_models('florida', self.fl_data, fl_feature_sets)
        self.results['florida'] = {
            'results': fl_results,
            'best_config': fl_best
        }

        # Train Pennsylvania models
        pa_feature_sets = self.get_pennsylvania_feature_sets()
        pa_results, pa_best = self.train_state_models('pennsylvania', self.pa_data, pa_feature_sets)
        self.results['pennsylvania'] = {
            'results': pa_results,
            'best_config': pa_best
        }

        # Compare to baseline
        self.compare_to_baseline()

        # Save models
        self.save_models()

        # Save reports
        self.save_training_report()

        print("\n" + "="*80)
        print("STATE-SPECIFIC MODEL TRAINING COMPLETE")
        print("="*80 + "\n")

        return self.results


if __name__ == '__main__':
    print("Training State-Specific Models v3.0")
    print("Optimizing for within-state site comparisons\n")

    trainer = StateSpecificModelTrainer()
    results = trainer.train_and_evaluate()

    print("\n✅ State-specific models v3 training completed successfully!")
