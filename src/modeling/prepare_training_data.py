"""
Data Preparation Module for Multi-State Dispensary Model

This module prepares the training dataset by:
1. Loading and filtering to training dispensaries (has_placer_data == True)
2. Handling missing values via median imputation
3. Creating state interaction features
4. Performing feature selection and VIF analysis
5. Scaling/normalizing features
6. Creating train/test splits

Author: Multi-State Dispensary Model Team
Date: October 2025
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
import json
from pathlib import Path


class DataPreparator:
    """
    Prepares training data for multi-state dispensary prediction model.

    Handles missing value imputation, feature engineering, scaling, and splits.
    """

    def __init__(self, data_path='data/processed/combined_with_competitive_features_corrected.csv',
                 target_column='corrected_visits'):
        """
        Initialize DataPreparator.

        Parameters:
        -----------
        data_path : str
            Path to combined dataset with competitive features (default: corrected dataset)
        target_column : str
            Target variable name (default: 'corrected_visits' for model v2)
        """
        self.data_path = data_path
        self.target_column = target_column
        self.df = None
        self.training_df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.scaler = None
        self.feature_names = None
        self.preparation_report = {}

    def load_and_filter(self):
        """
        Load data and filter to training dispensaries only.

        Returns:
        --------
        pd.DataFrame
            Training dispensaries (has_placer_data == True)
        """
        print("Loading data...")
        self.df = pd.read_csv(self.data_path)

        print(f"Total dispensaries loaded: {len(self.df)}")

        # Filter to training data only
        self.training_df = self.df[self.df['has_placer_data'] == True].copy()

        print(f"Training dispensaries: {len(self.training_df)}")
        print(f"  - Florida: {len(self.training_df[self.training_df.state == 'FL'])}")
        print(f"  - Pennsylvania: {len(self.training_df[self.training_df.state == 'PA'])}")

        # Verify we have the expected count
        assert len(self.training_df) == 741, f"Expected 741 training dispensaries, got {len(self.training_df)}"

        self.preparation_report['total_dispensaries'] = len(self.df)
        self.preparation_report['training_dispensaries'] = len(self.training_df)
        self.preparation_report['florida_training'] = len(self.training_df[self.training_df.state == 'FL'])
        self.preparation_report['pennsylvania_training'] = len(self.training_df[self.training_df.state == 'PA'])

        return self.training_df

    def handle_missing_values(self):
        """
        Handle missing values in all numeric features.

        Uses state-specific median imputation for all features with missing values.
        Skips columns that are 100% null (these will be filtered out in feature selection).

        Returns:
        --------
        pd.DataFrame
            Training data with imputed values
        """
        print("\nHandling missing values...")

        # Get all numeric columns
        numeric_cols = self.training_df.select_dtypes(include=[np.number]).columns

        missing_report = {}
        total_missing = 0

        for feature in numeric_cols:
            missing_count = self.training_df[feature].isna().sum()

            # Skip 100% null columns (will be dropped in feature selection)
            if missing_count == len(self.training_df):
                continue

            if missing_count > 0:
                total_missing += missing_count
                missing_report[feature] = {
                    'missing_count': int(missing_count),
                    'missing_pct': float(missing_count / len(self.training_df) * 100)
                }

                print(f"  {feature}: {missing_count} missing ({missing_count / len(self.training_df) * 100:.2f}%)")

                # Calculate state-specific medians
                fl_median = self.training_df[self.training_df.state == 'FL'][feature].median()
                pa_median = self.training_df[self.training_df.state == 'PA'][feature].median()

                missing_report[feature]['fl_median'] = float(fl_median) if not pd.isna(fl_median) else None
                missing_report[feature]['pa_median'] = float(pa_median) if not pd.isna(pa_median) else None

                # Impute with state-specific medians
                fl_mask = (self.training_df.state == 'FL') & (self.training_df[feature].isna())
                pa_mask = (self.training_df.state == 'PA') & (self.training_df[feature].isna())

                self.training_df.loc[fl_mask, feature] = fl_median
                self.training_df.loc[pa_mask, feature] = pa_median

                print(f"    Imputed FL missing with median: {fl_median:.2f}")
                print(f"    Imputed PA missing with median: {pa_median:.2f}")

        if total_missing == 0:
            print("  No missing values found!")

        self.preparation_report['missing_values'] = missing_report
        self.preparation_report['total_values_imputed'] = int(total_missing)

        # Verify no remaining NaN values (excluding 100% null columns)
        # Filter to only columns that aren't 100% null
        non_null_cols = [col for col in numeric_cols
                        if self.training_df[col].notna().sum() > 0]

        remaining_nan = self.training_df[non_null_cols].isna().sum().sum()
        if remaining_nan > 0:
            print(f"\n⚠️  Warning: {remaining_nan} NaN values remain after imputation!")
        else:
            print(f"\n✅ All missing values imputed successfully!")

        return self.training_df

    def create_state_interactions(self):
        """
        Create state interaction features for key predictors.

        Creates FL-specific and PA-specific versions of:
        - Multi-radius populations (pop_5mi, pop_20mi)
        - Competitor counts (competitors_5mi)
        - Market saturation (saturation_5mi)
        - Median household income

        Returns:
        --------
        pd.DataFrame
            Training data with state interaction features
        """
        print("\nCreating state interaction features...")

        # Create binary state indicators
        self.training_df['is_FL'] = (self.training_df['state'] == 'FL').astype(int)
        self.training_df['is_PA'] = (self.training_df['state'] == 'PA').astype(int)

        # Key features to create interactions for
        interaction_features = [
            'pop_5mi',
            'pop_20mi',
            'competitors_5mi',
            'saturation_5mi',
            'median_household_income'
        ]

        interaction_count = 0
        for feature in interaction_features:
            if feature in self.training_df.columns:
                # Create state-specific versions
                self.training_df[f'{feature}_FL'] = self.training_df[feature] * self.training_df['is_FL']
                self.training_df[f'{feature}_PA'] = self.training_df[feature] * self.training_df['is_PA']
                interaction_count += 2
                print(f"  Created: {feature}_FL, {feature}_PA")

        print(f"Total state interaction features created: {interaction_count}")

        self.preparation_report['state_interactions'] = {
            'count': interaction_count,
            'features': interaction_features
        }

        return self.training_df

    def select_features(self):
        """
        Select features for modeling, excluding identifiers and metadata.

        Only includes numeric features suitable for regression modeling.

        Returns:
        --------
        list
            List of feature column names for modeling
        """
        print("\nSelecting features for modeling...")

        # Use configured target variable (model v2 uses 'corrected_visits')
        target = self.target_column

        # Columns to exclude (identifiers, metadata, data quality flags)
        exclude_patterns = [
            'regulator_', 'placer_', 'census_geoid', 'census_tract_name',
            'census_state_fips', 'census_county_fips', 'census_tract_fips',
            'has_placer_data', 'census_data_complete', 'census_api_error',
            'match_score', 'match_type', 'match_details', 'data_source',
            'chain_name', 'chain_id', 'dispensary_id',
            'latitude', 'longitude',  # Exclude raw coordinates (captured in census features)
            'visits_per_sq_ft',  # Exclude UNCORRECTED derived variable (legacy)
            'corrected_visits_per_sq_ft',  # Exclude derived target variable
            'corrected_visits_step1',  # Exclude intermediate correction step (DATA LEAKAGE!)
            'visits',  # Exclude UNCORRECTED target (legacy - use corrected_visits instead)
            'state',  # Exclude state (we use is_FL/is_PA instead)
            '_date', '_name', '_number', '_type', '_abbr', '_census',  # Exclude text/date columns
            'product_', 'applicant_', 'permit_', 'license_', 'region',  # Exclude categorical PA columns
            'temporal_adjustment', 'correction_', 'maturity_', 'months_operational'  # Exclude correction metadata
        ]

        # Start with all columns
        candidate_features = []

        for col in self.training_df.columns:
            # Skip target variable
            if col == target:
                continue

            # Skip excluded patterns
            if any(pattern in col for pattern in exclude_patterns):
                continue

            # Only include numeric columns with non-zero variance
            if pd.api.types.is_numeric_dtype(self.training_df[col]):
                # Skip columns that are entirely NaN
                if self.training_df[col].notna().sum() == 0:
                    print(f"  Skipping all-NaN column: {col}")
                    continue
                candidate_features.append(col)
            else:
                print(f"  Skipping non-numeric column: {col}")

        print(f"Selected {len(candidate_features)} numeric features for modeling")

        # Validation: Warn if using legacy columns
        if target == 'visits':
            print("\n⚠️  WARNING: Using UNCORRECTED 'visits' as target!")
            print("   For model v2, use 'corrected_visits' instead.")

        self.feature_names = candidate_features
        self.preparation_report['num_features'] = len(candidate_features)
        self.preparation_report['target_variable'] = target

        return candidate_features

    def calculate_vif(self, X):
        """
        Calculate Variance Inflation Factor (VIF) to detect multicollinearity.

        Parameters:
        -----------
        X : pd.DataFrame
            Feature matrix

        Returns:
        --------
        pd.DataFrame
            VIF scores for each feature
        """
        print("\nCalculating VIF (Variance Inflation Factor)...")
        print("This may take a minute for 40+ features...")

        vif_data = pd.DataFrame()
        vif_data["feature"] = X.columns

        # Calculate VIF for each feature
        vif_scores = []
        for i in range(len(X.columns)):
            try:
                vif = variance_inflation_factor(X.values, i)
                vif_scores.append(vif)
            except Exception as e:
                print(f"  Warning: Could not calculate VIF for {X.columns[i]}: {e}")
                vif_scores.append(np.nan)

        vif_data["VIF"] = vif_scores

        # Sort by VIF
        vif_data = vif_data.sort_values('VIF', ascending=False)

        # Report high VIF features (> 10 indicates multicollinearity concern)
        high_vif = vif_data[vif_data['VIF'] > 10]

        if len(high_vif) > 0:
            print(f"\nWarning: {len(high_vif)} features with VIF > 10 (multicollinearity concern):")
            print(high_vif.head(10).to_string(index=False))
        else:
            print("No features with VIF > 10 (good!)")

        self.preparation_report['vif_analysis'] = {
            'high_vif_count': len(high_vif),
            'max_vif': float(vif_data['VIF'].max()) if not pd.isna(vif_data['VIF'].max()) else None,
            'mean_vif': float(vif_data['VIF'].mean()) if not pd.isna(vif_data['VIF'].mean()) else None
        }

        return vif_data

    def create_train_test_split(self, test_size=0.2, random_state=42):
        """
        Create stratified train/test split.

        Parameters:
        -----------
        test_size : float
            Proportion of data for test set (default 0.2)
        random_state : int
            Random seed for reproducibility

        Returns:
        --------
        tuple
            (X_train, X_test, y_train, y_test)
        """
        print(f"\nCreating train/test split ({int((1-test_size)*100)}/{int(test_size*100)})...")

        # Prepare feature matrix and target
        X = self.training_df[self.feature_names]
        y = self.training_df[self.target_column]  # Use configured target (corrected_visits for v2)

        # Stratify by state to maintain FL/PA ratio
        stratify = self.training_df['state']

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify
        )

        print(f"Training set: {len(self.X_train)} dispensaries")
        print(f"  - FL: {len(self.X_train[self.X_train['is_FL'] == 1])}")
        print(f"  - PA: {len(self.X_train[self.X_train['is_PA'] == 1])}")
        print(f"Test set: {len(self.X_test)} dispensaries")
        print(f"  - FL: {len(self.X_test[self.X_test['is_FL'] == 1])}")
        print(f"  - PA: {len(self.X_test[self.X_test['is_PA'] == 1])}")

        self.preparation_report['train_test_split'] = {
            'train_size': len(self.X_train),
            'test_size': len(self.X_test),
            'train_fl': len(self.X_train[self.X_train['is_FL'] == 1]),
            'train_pa': len(self.X_train[self.X_train['is_PA'] == 1]),
            'test_fl': len(self.X_test[self.X_test['is_FL'] == 1]),
            'test_pa': len(self.X_test[self.X_test['is_PA'] == 1]),
            'test_size_ratio': test_size,
            'random_state': random_state
        }

        return self.X_train, self.X_test, self.y_train, self.y_test

    def scale_features(self):
        """
        Scale features using StandardScaler (mean=0, std=1).

        Fits scaler on training data only to prevent data leakage.

        Returns:
        --------
        tuple
            (X_train_scaled, X_test_scaled)
        """
        print("\nScaling features (StandardScaler)...")

        self.scaler = StandardScaler()

        # Fit on training data only
        X_train_scaled = self.scaler.fit_transform(self.X_train)
        X_test_scaled = self.scaler.transform(self.X_test)

        # Convert back to DataFrames to preserve column names
        X_train_scaled = pd.DataFrame(X_train_scaled, columns=self.feature_names, index=self.X_train.index)
        X_test_scaled = pd.DataFrame(X_test_scaled, columns=self.feature_names, index=self.X_test.index)

        print(f"Features scaled: {len(self.feature_names)}")

        self.preparation_report['scaling'] = {
            'method': 'StandardScaler',
            'features_scaled': len(self.feature_names)
        }

        return X_train_scaled, X_test_scaled

    def prepare_data(self, test_size=0.2, random_state=42, scale=True):
        """
        Execute full data preparation pipeline.

        Parameters:
        -----------
        test_size : float
            Proportion of data for test set
        random_state : int
            Random seed for reproducibility
        scale : bool
            Whether to scale features for final test evaluation (default True)
            Note: For proper CV, models should use sklearn Pipeline to avoid data leakage

        Returns:
        --------
        dict
            Dictionary containing prepared data and metadata:
            {
                'X_train': Training features (unscaled for Pipeline),
                'X_test': Test features (unscaled for Pipeline),
                'y_train': Training target,
                'y_test': Test target,
                'feature_names': List of feature names,
                'scaler': Fitted StandardScaler for reference (if scale=True),
                'vif_data': VIF analysis results,
                'preparation_report': Full preparation report,
                'training_df': Original training dataframe (for state labels)
            }
            Note: Pipeline will handle scaling internally for both CV and test evaluation
        """
        # Step 1: Load and filter
        self.load_and_filter()

        # Step 2: Handle missing values
        self.handle_missing_values()

        # Step 3: Create state interactions
        self.create_state_interactions()

        # Step 4: Select features
        self.select_features()

        # Step 5: Create train/test split
        self.create_train_test_split(test_size=test_size, random_state=random_state)

        # Step 6: Calculate VIF on training data (before scaling)
        vif_data = self.calculate_vif(self.X_train)

        # Step 7: Keep test data unscaled for Pipeline
        # Both training and test data stay unscaled for proper CV with Pipeline
        # The Pipeline will handle scaling internally
        X_train_out = self.X_train.copy()
        X_test_out = self.X_test.copy()  # Unscaled! Pipeline will scale

        # Fit scaler on training data for metadata/reference only
        if scale:
            scaler = StandardScaler()
            scaler.fit(self.X_train)
            self.scaler = scaler
        else:
            self.scaler = None

        print("\n" + "="*60)
        print("Data preparation complete!")
        print(f"Training dispensaries: {len(X_train_out)} (unscaled for Pipeline)")
        print(f"Test dispensaries: {len(X_test_out)} (unscaled for Pipeline)")
        print(f"Features: {len(self.feature_names)}")
        print(f"Note: Pipeline will handle scaling internally")
        print("="*60 + "\n")

        return {
            'X_train': X_train_out,
            'X_test': X_test_out,
            'y_train': self.y_train,
            'y_test': self.y_test,
            'feature_names': self.feature_names,
            'scaler': self.scaler,
            'vif_data': vif_data,
            'preparation_report': self.preparation_report,
            'training_df': self.training_df  # Include for state labels
        }

    def scale_test_only(self):
        """
        Fit scaler on training data and transform test data only.

        Training data is left unscaled for proper cross-validation with Pipeline.

        Returns:
        --------
        tuple
            (X_test_scaled, scaler)
        """
        print("\nScaling test set only (training data stays unscaled for CV)...")

        scaler = StandardScaler()
        scaler.fit(self.X_train)
        X_test_scaled = scaler.transform(self.X_test)

        # Convert back to DataFrame
        X_test_scaled = pd.DataFrame(X_test_scaled, columns=self.feature_names, index=self.X_test.index)

        print(f"Scaler fitted on training data ({len(self.X_train)} samples)")
        print(f"Test data scaled ({len(self.X_test)} samples)")

        return X_test_scaled, scaler

    def save_report(self, output_path='data/models/data_preparation_report.json'):
        """
        Save preparation report to JSON file.

        Parameters:
        -----------
        output_path : str
            Path to save report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.preparation_report, f, indent=2)

        print(f"Preparation report saved to: {output_path}")


if __name__ == '__main__':
    # Example usage
    print("Multi-State Dispensary Model - Data Preparation (Model v2)")
    print("=" * 60)

    # Initialize preparator with corrected dataset and target
    preparator = DataPreparator(
        data_path='data/processed/combined_with_competitive_features_corrected.csv',
        target_column='corrected_visits'
    )

    # Prepare data
    prepared_data = preparator.prepare_data(
        test_size=0.2,
        random_state=42,
        scale=True
    )

    # Save report
    preparator.save_report('data/models/data_preparation_report_v2.json')

    print("\nData preparation completed successfully!")
    print(f"Target variable: {preparator.target_column} (ANNUAL visits)")
