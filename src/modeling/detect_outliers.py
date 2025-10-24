"""
Outlier Detection and Analysis Script

Purpose: Identify potential outliers in training data for model improvement
Approach: Multi-method detection (statistical, business logic, residual-based)
Output: Detailed analysis report with recommendations for removal

Author: Claude Code
Date: October 24, 2025
"""

import pandas as pd
import numpy as np
from scipy import stats
import pickle
from pathlib import Path

class OutlierDetector:
    """Detect and analyze outliers in dispensary training data."""

    def __init__(self, data_path='data/processed/combined_with_competitive_features.csv',
                 model_path='data/models/multi_state_model_v1.pkl'):
        """Initialize outlier detector."""
        self.data_path = data_path
        self.model_path = model_path
        self.df = None
        self.training_df = None
        self.model = None
        self.feature_names = None

    def load_data(self):
        """Load dataset and filter to training data."""
        print("Loading data...")
        self.df = pd.read_csv(self.data_path)
        self.training_df = self.df[self.df['has_placer_data'] == True].copy()
        print(f"  Total dispensaries: {len(self.df)}")
        print(f"  Training dispensaries: {len(self.training_df)}")
        print()

    def load_model(self):
        """Load trained model for residual analysis."""
        try:
            print("Loading model...")
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            print(f"  Model loaded: {len(self.feature_names)} features")
            print()
        except FileNotFoundError:
            print("  Model not found - residual analysis will be skipped")
            print()

    def detect_statistical_outliers(self, n_std=3):
        """Detect outliers using z-score method (±n standard deviations)."""
        print("="*70)
        print("STATISTICAL OUTLIERS (Z-Score Method)")
        print("="*70)
        print()

        visits = self.training_df['visits']
        mean_visits = visits.mean()
        std_visits = visits.std()

        # Calculate z-scores
        z_scores = np.abs((visits - mean_visits) / std_visits)

        # Identify outliers
        outliers = self.training_df[z_scores > n_std].copy()
        outliers['z_score'] = z_scores[z_scores > n_std]
        outliers = outliers.sort_values('z_score', ascending=False)

        print(f"Threshold: ±{n_std} standard deviations")
        print(f"Mean visits: {mean_visits:,.0f}")
        print(f"Std deviation: {std_visits:,.0f}")
        print(f"Upper threshold: {mean_visits + n_std * std_visits:,.0f}")
        print(f"Lower threshold: {max(0, mean_visits - n_std * std_visits):,.0f}")
        print()
        print(f"Outliers found: {len(outliers)}")

        if len(outliers) > 0:
            print()
            print("Statistical outliers:")
            cols = ['state', 'regulator_name', 'visits', 'sq_ft',
                   'visits_per_sq_ft', 'z_score', 'competitors_5mi']
            print(outliers[cols].to_string(index=False))

        print()
        return outliers

    def detect_business_logic_outliers(self):
        """Detect outliers using business logic rules."""
        print("="*70)
        print("BUSINESS LOGIC OUTLIERS")
        print("="*70)
        print()

        outliers_dict = {}

        # Very large stores (>10,000 sq ft)
        very_large = self.training_df[self.training_df['sq_ft'] > 10000].copy()
        outliers_dict['very_large_sqft'] = very_large
        print(f"Very large stores (>10,000 sq ft): {len(very_large)}")
        if len(very_large) > 0:
            cols = ['state', 'regulator_name', 'sq_ft', 'visits', 'visits_per_sq_ft']
            print(very_large[cols].to_string(index=False))
        print()

        # Very small stores (<500 sq ft)
        very_small = self.training_df[self.training_df['sq_ft'] < 500].copy()
        outliers_dict['very_small_sqft'] = very_small
        print(f"Very small stores (<500 sq ft): {len(very_small)}")
        if len(very_small) > 0:
            cols = ['state', 'regulator_name', 'sq_ft', 'visits', 'visits_per_sq_ft']
            print(very_small[cols].to_string(index=False))
        print()

        # Very high traffic (>200k visits/month)
        very_high_traffic = self.training_df[self.training_df['visits'] > 200000].copy()
        outliers_dict['very_high_traffic'] = very_high_traffic
        print(f"Very high traffic (>200k visits/month): {len(very_high_traffic)}")
        if len(very_high_traffic) > 0:
            cols = ['state', 'regulator_name', 'visits', 'sq_ft',
                   'visits_per_sq_ft', 'competitors_5mi']
            print(very_high_traffic[cols].to_string(index=False))
        print()

        # Very low traffic (<5k visits/month) - LIKELY DATA QUALITY ISSUES
        very_low_traffic = self.training_df[self.training_df['visits'] < 5000].copy()
        outliers_dict['very_low_traffic'] = very_low_traffic
        print(f"Very low traffic (<5k visits/month): {len(very_low_traffic)} ⚠️")
        if len(very_low_traffic) > 0:
            print("  ** These are prime candidates for data quality review **")
            cols = ['state', 'regulator_name', 'regulator_city', 'visits',
                   'sq_ft', 'visits_per_sq_ft', 'competitors_5mi',
                   'latitude', 'longitude']
            print(very_low_traffic[cols].to_string(index=False))
        print()

        # Extremely low visits per sq ft (<2)
        low_efficiency = self.training_df[
            self.training_df['visits_per_sq_ft'] < 2
        ].copy()
        outliers_dict['low_efficiency'] = low_efficiency
        print(f"Low efficiency (<2 visits/sq ft): {len(low_efficiency)}")
        if len(low_efficiency) > 0:
            cols = ['state', 'regulator_name', 'visits', 'sq_ft',
                   'visits_per_sq_ft', 'competitors_5mi']
            print(low_efficiency[cols].to_string(index=False))
        print()

        return outliers_dict

    def detect_residual_outliers(self, threshold=3):
        """Detect outliers based on model residuals (prediction errors)."""
        if self.model is None:
            print("Model not loaded - skipping residual analysis")
            print()
            return None

        print("="*70)
        print("RESIDUAL-BASED OUTLIERS (Model Prediction Errors)")
        print("="*70)
        print()

        # Generate state indicator features
        self.training_df['is_FL'] = (self.training_df['state'] == 'FL').astype(int)
        self.training_df['is_PA'] = (self.training_df['state'] == 'PA').astype(int)

        # Generate state interaction features
        base_features = ['pop_5mi', 'pop_20mi', 'competitors_5mi',
                        'saturation_5mi', 'median_household_income']
        for feat in base_features:
            if feat in self.training_df.columns:
                self.training_df[f'{feat}_FL'] = self.training_df[feat] * self.training_df['is_FL']
                self.training_df[f'{feat}_PA'] = self.training_df[feat] * self.training_df['is_PA']

        # Get features for prediction
        try:
            X = self.training_df[self.feature_names]

            # Check for NaN values
            if X.isna().any().any():
                nan_cols = X.columns[X.isna().any()].tolist()
                print(f"  ⚠️  Features contain NaN values - skipping residual analysis")
                print(f"  Columns with NaN: {nan_cols}")
                print()
                return None

        except KeyError as e:
            print(f"  ⚠️  Missing features - cannot perform residual analysis")
            print(f"  Error: {e}")
            print()
            return None

        y_actual = self.training_df['visits']

        # Make predictions
        y_pred = self.model.predict(X)

        # Calculate residuals
        residuals = y_actual - y_pred
        residual_pct = (residuals / y_actual) * 100

        # Standardize residuals
        z_scores = np.abs(stats.zscore(residuals))

        # Find outliers
        outlier_mask = z_scores > threshold
        outliers = self.training_df[outlier_mask].copy()
        outliers['actual_visits'] = y_actual[outlier_mask]
        outliers['predicted_visits'] = y_pred[outlier_mask]
        outliers['residual'] = residuals[outlier_mask].values
        outliers['residual_pct'] = residual_pct[outlier_mask].values
        outliers['residual_z_score'] = z_scores[outlier_mask]

        # Sort by absolute residual
        outliers = outliers.sort_values('residual_z_score', ascending=False)

        print(f"Threshold: ±{threshold} standard deviations of residuals")
        print(f"Mean residual: {residuals.mean():,.0f}")
        print(f"Std residual: {residuals.std():,.0f}")
        print(f"Outliers found: {len(outliers)}")
        print()

        if len(outliers) > 0:
            # Split into over-predicted and under-predicted
            over_predicted = outliers[outliers['residual'] < 0]
            under_predicted = outliers[outliers['residual'] > 0]

            print(f"Over-predicted (model too high): {len(over_predicted)}")
            if len(over_predicted) > 0:
                cols = ['state', 'regulator_name', 'actual_visits',
                       'predicted_visits', 'residual', 'residual_pct']
                print(over_predicted[cols].head(10).to_string(index=False))
            print()

            print(f"Under-predicted (model too low): {len(under_predicted)}")
            if len(under_predicted) > 0:
                cols = ['state', 'regulator_name', 'actual_visits',
                       'predicted_visits', 'residual', 'residual_pct']
                print(under_predicted[cols].head(10).to_string(index=False))
            print()

        return outliers

    def generate_removal_recommendations(self,
                                        statistical_outliers,
                                        business_outliers,
                                        residual_outliers=None):
        """Generate recommendations for outlier removal."""
        print("="*70)
        print("OUTLIER REMOVAL RECOMMENDATIONS")
        print("="*70)
        print()

        recommendations = []

        # Very low traffic sites (<5k visits) - PRIORITY
        very_low = business_outliers.get('very_low_traffic', pd.DataFrame())
        if len(very_low) > 0:
            print("🔴 HIGH PRIORITY: Very low traffic sites (<5k visits)")
            print(f"   Count: {len(very_low)}")
            print("   Reason: Likely data quality issues or special circumstances")
            print("   Recommendation: MANUAL REVIEW REQUIRED")
            print("   Action:")
            print("     1. Check coordinates (correct location?)")
            print("     2. Verify square footage (data entry error?)")
            print("     3. Research store status (closed, temporary, new?)")
            print("     4. If confirmed error: REMOVE")
            print("     5. If legitimate low performer: KEEP")
            print()

            for idx, row in very_low.iterrows():
                recommendations.append({
                    'dispensary': row['regulator_name'],
                    'state': row['state'],
                    'city': row.get('regulator_city', 'Unknown'),
                    'visits': row['visits'],
                    'sq_ft': row['sq_ft'],
                    'lat': row['latitude'],
                    'lon': row['longitude'],
                    'priority': 'HIGH',
                    'reason': 'Very low traffic (<5k)',
                    'action': 'Manual review required'
                })

        # Very large stores (>10k sq ft) - LOW PRIORITY
        very_large = business_outliers.get('very_large_sqft', pd.DataFrame())
        if len(very_large) > 0:
            print("🟢 LOW PRIORITY: Very large stores (>10k sq ft)")
            print(f"   Count: {len(very_large)}")
            print("   Reason: Legitimate flagship stores")
            print("   Recommendation: KEEP (valuable data points)")
            print()

        # Very high traffic (>200k) - LOW PRIORITY
        very_high = business_outliers.get('very_high_traffic', pd.DataFrame())
        if len(very_high) > 0:
            print("🟢 LOW PRIORITY: Very high traffic (>200k)")
            print(f"   Count: {len(very_high)}")
            print("   Reason: Legitimate high performers")
            print("   Recommendation: KEEP (valuable data points)")
            print()

        # Low efficiency (<2 visits/sq ft)
        low_eff = business_outliers.get('low_efficiency', pd.DataFrame())
        if len(low_eff) > 0:
            print("🟡 MEDIUM PRIORITY: Low efficiency (<2 visits/sq ft)")
            print(f"   Count: {len(low_eff)}")
            print("   Reason: Unusual performance ratio")
            print("   Recommendation: MANUAL REVIEW (overlap with low traffic)")
            print()

        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total outliers requiring manual review: {len(very_low)}")
        print(f"Recommended for potential removal: {len(very_low)} (pending review)")
        print(f"Recommended to keep: {len(very_large) + len(very_high)}")
        print()

        return pd.DataFrame(recommendations) if recommendations else None

    def run_full_analysis(self):
        """Run complete outlier detection analysis."""
        self.load_data()
        self.load_model()

        # Run all detection methods
        statistical = self.detect_statistical_outliers()
        business = self.detect_business_logic_outliers()
        residual = self.detect_residual_outliers()

        # Generate recommendations
        recommendations = self.generate_removal_recommendations(
            statistical, business, residual
        )

        # Save recommendations if any
        if recommendations is not None and len(recommendations) > 0:
            output_path = 'data/processed/outlier_review_candidates.csv'
            recommendations.to_csv(output_path, index=False)
            print(f"Outlier candidates saved to: {output_path}")
            print()

        return {
            'statistical': statistical,
            'business': business,
            'residual': residual,
            'recommendations': recommendations
        }


def main():
    """Run outlier detection analysis."""
    print("\n")
    print("="*70)
    print("OUTLIER DETECTION AND ANALYSIS")
    print("="*70)
    print()

    detector = OutlierDetector()
    results = detector.run_full_analysis()

    print("\n")
    print("="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Review data/processed/outlier_review_candidates.csv")
    print("2. Manually verify coordinates and data quality for flagged sites")
    print("3. Document removal decisions")
    print("4. Create cleaned dataset: combined_with_competitive_features_v2.csv")
    print("5. Retrain model and compare R² improvement")
    print()


if __name__ == "__main__":
    main()
