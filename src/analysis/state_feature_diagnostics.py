"""
State-Specific Feature Diagnostics

Analyzes which features correlate with dispensary performance within each state.
This helps identify if current features have predictive power for within-state comparisons.

Usage:
    python src/analysis/state_feature_diagnostics.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr


def load_training_data():
    """Load training data with corrected visits."""
    project_root = Path(__file__).parent.parent.parent
    data_file = project_root / "data" / "processed" / "combined_with_competitive_features_corrected.csv"

    df = pd.read_csv(data_file)

    # Filter to training dispensaries only
    training = df[df['has_placer_data'] == True].copy()

    print(f"✅ Loaded {len(training)} training dispensaries")
    print(f"   - Florida: {len(training[training['state'] == 'FL'])}")
    print(f"   - Pennsylvania: {len(training[training['state'] == 'PA'])}")
    print()

    return training


def analyze_state_correlations(df, state):
    """Calculate feature correlations with corrected_visits for a specific state."""

    state_data = df[df['state'] == state].copy()

    # Select numeric features (exclude IDs, dates, flags)
    exclude_cols = [
        'id', 'dispensary_id', 'name', 'address', 'city', 'state', 'zipcode',
        'latitude', 'longitude', 'license_number', 'license_type',
        'has_placer_data', 'months_operational', 'temporal_adjustment_factor',
        'placer_visits', 'corrected_visits'  # Target variable
    ]

    feature_cols = [col for col in state_data.columns
                   if col not in exclude_cols
                   and state_data[col].dtype in ['int64', 'float64']]

    # Calculate correlations
    correlations = []
    for feature in feature_cols:
        # Remove missing values for this feature
        valid_data = state_data[[feature, 'corrected_visits']].dropna()

        if len(valid_data) < 10:  # Need at least 10 samples
            continue

        # Calculate Pearson correlation
        corr, p_value = pearsonr(valid_data[feature], valid_data['corrected_visits'])

        correlations.append({
            'feature': feature,
            'correlation': corr,
            'abs_correlation': abs(corr),
            'p_value': p_value,
            'n_samples': len(valid_data)
        })

    # Convert to DataFrame and sort by absolute correlation
    corr_df = pd.DataFrame(correlations)
    corr_df = corr_df.sort_values('abs_correlation', ascending=False)

    return corr_df


def plot_top_correlations(corr_df, state, top_n=15):
    """Plot top N features by absolute correlation."""

    top_features = corr_df.head(top_n).copy()

    # Create horizontal bar plot
    fig, ax = plt.subplots(figsize=(10, 8))

    colors = ['green' if x > 0 else 'red' for x in top_features['correlation']]

    ax.barh(range(len(top_features)), top_features['correlation'], color=colors, alpha=0.6)
    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features['feature'])
    ax.set_xlabel('Correlation with Annual Visits')
    ax.set_title(f'Top {top_n} Features - {state} Within-State Correlation\n(Green=Positive, Red=Negative)')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()

    return fig


def analyze_variance_explained(df, state, top_features):
    """Calculate R² for top individual features within a state."""

    state_data = df[df['state'] == state].copy()

    results = []
    for feature in top_features:
        valid_data = state_data[[feature, 'corrected_visits']].dropna()

        if len(valid_data) < 10:
            continue

        # Calculate R² (correlation squared)
        corr = valid_data[feature].corr(valid_data['corrected_visits'])
        r_squared = corr ** 2

        results.append({
            'feature': feature,
            'r_squared': r_squared,
            'variance_explained_pct': r_squared * 100
        })

    return pd.DataFrame(results).sort_values('r_squared', ascending=False)


def main():
    """Run state-specific feature diagnostics."""

    print("="*70)
    print("STATE-SPECIFIC FEATURE DIAGNOSTICS")
    print("="*70)
    print()

    # Load data
    df = load_training_data()

    # Create output directory
    output_dir = Path(__file__).parent.parent.parent / "analysis_output" / "state_diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Analyze each state
    for state in ['FL', 'PA']:
        print(f"\n{'='*70}")
        print(f"{state} - WITHIN-STATE FEATURE ANALYSIS")
        print(f"{'='*70}\n")

        # Calculate correlations
        corr_df = analyze_state_correlations(df, state)

        # Display top 20 features
        print(f"Top 20 Features by Correlation (n={len(df[df['state']==state])} dispensaries):\n")
        print(corr_df.head(20)[['feature', 'correlation', 'p_value']].to_string(index=False))
        print()

        # Calculate variance explained by top features
        top_features = corr_df.head(10)['feature'].tolist()
        variance_df = analyze_variance_explained(df, state, top_features)

        print(f"\nVariance Explained by Top Features (Individual R²):\n")
        print(variance_df.head(10).to_string(index=False))
        print()

        # Save results
        corr_df.to_csv(output_dir / f"{state}_feature_correlations.csv", index=False)
        variance_df.to_csv(output_dir / f"{state}_variance_explained.csv", index=False)

        # Create visualization
        fig = plot_top_correlations(corr_df, state, top_n=15)
        fig.savefig(output_dir / f"{state}_top_features.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

        print(f"✅ Saved results to: {output_dir}")

    # Summary comparison
    print(f"\n{'='*70}")
    print("SUMMARY: FL vs PA Feature Strength")
    print(f"{'='*70}\n")

    fl_corr = analyze_state_correlations(df, 'FL')
    pa_corr = analyze_state_correlations(df, 'PA')

    fl_max = fl_corr['abs_correlation'].max()
    pa_max = pa_corr['abs_correlation'].max()

    fl_top_feature = fl_corr.iloc[0]['feature']
    pa_top_feature = pa_corr.iloc[0]['feature']

    print(f"Florida:")
    print(f"  - Strongest feature: {fl_top_feature}")
    print(f"  - Max correlation: {fl_max:.4f}")
    print(f"  - Max variance explained: {fl_max**2*100:.2f}%")
    print()

    print(f"Pennsylvania:")
    print(f"  - Strongest feature: {pa_top_feature}")
    print(f"  - Max correlation: {pa_max:.4f}")
    print(f"  - Max variance explained: {pa_max**2*100:.2f}%")
    print()

    print("="*70)
    print("Analysis complete! Check analysis_output/state_diagnostics/ for detailed results.")
    print("="*70)


if __name__ == "__main__":
    main()
