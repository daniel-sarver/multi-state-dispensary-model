"""
Population Density Analysis Script

Investigates the population density paradox:
1. Is there a non-linear relationship (e.g., optimal range)?
2. Is population_density confounded by competitor counts?

Author: Multi-State Dispensary Model Team
Date: October 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures
from scipy import stats

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)


def load_data():
    """Load training data."""
    df = pd.read_csv('data/processed/combined_with_competitive_features.csv')
    training_df = df[df['has_placer_data'] == True].copy()
    return training_df


def analyze_pop_density_correlation(df):
    """
    Analyze correlation between population_density and other features.
    """
    print("="*60)
    print("POPULATION DENSITY CORRELATION ANALYSIS")
    print("="*60 + "\n")

    # Key features to check correlation with
    features_to_check = [
        'visits', 'competitors_1mi', 'competitors_3mi', 'competitors_5mi',
        'competitors_10mi', 'competitors_20mi', 'competition_weighted_20mi',
        'saturation_5mi', 'pop_5mi', 'pop_20mi'
    ]

    correlations = {}
    for feature in features_to_check:
        if feature in df.columns:
            corr = df['population_density'].corr(df[feature])
            correlations[feature] = corr

    # Sort by absolute correlation
    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

    print("Population Density Correlations:")
    print("-" * 60)
    for feature, corr in sorted_corr:
        print(f"  {feature:30s}: {corr:7.4f}")

    return correlations


def test_nonlinear_relationship(df):
    """
    Test for non-linear (quadratic) relationship between population_density and visits.
    """
    print("\n" + "="*60)
    print("NON-LINEAR RELATIONSHIP TEST (QUADRATIC)")
    print("="*60 + "\n")

    # Prepare data
    X_linear = df[['population_density']].values
    X_quad = np.column_stack([X_linear, X_linear**2])
    y = df['visits'].values

    # Remove NaN
    valid_mask = ~(np.isnan(X_linear).any(axis=1) | np.isnan(y))
    X_linear_clean = X_linear[valid_mask]
    X_quad_clean = X_quad[valid_mask]
    y_clean = y[valid_mask]

    # Linear model
    scaler_linear = StandardScaler()
    X_linear_scaled = scaler_linear.fit_transform(X_linear_clean)
    model_linear = Ridge(alpha=1000)
    model_linear.fit(X_linear_scaled, y_clean)
    r2_linear = model_linear.score(X_linear_scaled, y_clean)

    # Quadratic model
    scaler_quad = StandardScaler()
    X_quad_scaled = scaler_quad.fit_transform(X_quad_clean)
    model_quad = Ridge(alpha=1000)
    model_quad.fit(X_quad_scaled, y_clean)
    r2_quad = model_quad.score(X_quad_scaled, y_clean)

    print(f"Linear Model R²:    {r2_linear:.4f}")
    print(f"Quadratic Model R²: {r2_quad:.4f}")
    print(f"R² Improvement:     {r2_quad - r2_linear:.4f} ({(r2_quad - r2_linear) / r2_linear * 100:.1f}%)")

    if r2_quad > r2_linear + 0.01:
        print("\n✅ Evidence of non-linear relationship (quadratic fits better)")
    else:
        print("\n⚠️  Little evidence of non-linear relationship")

    # Find optimal range if quadratic
    if r2_quad > r2_linear + 0.01:
        # Optimal point: -b / (2a) for ax^2 + bx + c
        coef_quad = model_quad.coef_[1]  # Coefficient of squared term
        coef_linear = model_quad.coef_[0]  # Coefficient of linear term

        if coef_quad < 0:  # Concave down (has maximum)
            # In scaled space
            optimal_scaled = -coef_linear / (2 * coef_quad)
            # Transform back to original scale
            optimal_density = optimal_scaled * scaler_quad.scale_[0] + scaler_quad.mean_[0]
            print(f"\n📍 Optimal population density: {optimal_density:,.0f} people/sq mi")
            print(f"   (Interpretation: Visits peak around this density)")
        else:
            print("\n⚠️  Quadratic is concave up (monotonic relationship)")

    return {'linear_r2': r2_linear, 'quadratic_r2': r2_quad}


def test_competitor_confounding(df):
    """
    Test if population_density's negative coefficient is due to competitor confounding.
    """
    print("\n" + "="*60)
    print("COMPETITOR CONFOUNDING TEST")
    print("="*60 + "\n")

    # Model 1: pop_density only
    features_model1 = ['population_density']
    # Model 2: pop_density + competitors
    features_model2 = ['population_density', 'competitors_5mi', 'saturation_5mi']
    # Model 3: competitors only
    features_model3 = ['competitors_5mi', 'saturation_5mi']

    # Prepare data
    y = df['visits'].values

    results = {}

    for model_name, features in [
        ('Pop Density Only', features_model1),
        ('Pop Density + Competitors', features_model2),
        ('Competitors Only', features_model3)
    ]:
        X = df[features].values
        valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X_clean = X[valid_mask]
        y_clean = y[valid_mask]

        # Train Ridge model
        model = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=1000))
        ])
        model.fit(X_clean, y_clean)
        r2 = model.score(X_clean, y_clean)

        # Get coefficients
        coeffs = model.named_steps['ridge'].coef_

        print(f"{model_name}:")
        print(f"  R² = {r2:.4f}")
        for i, feature in enumerate(features):
            print(f"  {feature:30s}: {coeffs[i]:10.2f}")
        print()

        results[model_name] = {'r2': r2, 'coefficients': dict(zip(features, coeffs))}

    # Analysis
    print("Analysis:")
    print("-" * 60)

    pop_density_coef_alone = results['Pop Density Only']['coefficients']['population_density']
    pop_density_coef_with_comp = results['Pop Density + Competitors']['coefficients']['population_density']

    print(f"Population Density coefficient:")
    print(f"  Alone:            {pop_density_coef_alone:10.2f}")
    print(f"  With Competitors: {pop_density_coef_with_comp:10.2f}")
    print(f"  Change:           {pop_density_coef_with_comp - pop_density_coef_alone:10.2f}")

    if abs(pop_density_coef_with_comp) < abs(pop_density_coef_alone):
        reduction_pct = (1 - abs(pop_density_coef_with_comp) / abs(pop_density_coef_alone)) * 100
        print(f"\n✅ Competitor variables explain {reduction_pct:.1f}% of pop_density's effect")
        print("   (Evidence that negative coefficient is due to competition in dense areas)")
    else:
        print(f"\n⚠️  Pop_density coefficient remains strong even with competitors")
        print("   (Population density has independent negative effect)")

    return results


def create_binned_analysis(df):
    """
    Create binned analysis to visualize relationship.
    """
    print("\n" + "="*60)
    print("BINNED ANALYSIS (POPULATION DENSITY RANGES)")
    print("="*60 + "\n")

    # Create density bins
    df_analysis = df[['population_density', 'visits', 'competitors_5mi', 'saturation_5mi']].copy()
    df_analysis = df_analysis.dropna()

    # Create percentile bins
    df_analysis['density_bin'] = pd.qcut(
        df_analysis['population_density'],
        q=5,
        labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'],
        duplicates='drop'
    )

    # Calculate statistics by bin
    bin_stats = df_analysis.groupby('density_bin').agg({
        'population_density': ['mean', 'count'],
        'visits': ['mean', 'median', 'std'],
        'competitors_5mi': 'mean',
        'saturation_5mi': 'mean'
    })

    print("Population Density Bins:")
    print(bin_stats.to_string())

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))

    # Plot 1: Scatter plot with binned means
    ax1 = axes[0, 0]
    ax1.scatter(df_analysis['population_density'], df_analysis['visits'], alpha=0.3, s=20)
    bin_means = df_analysis.groupby('density_bin')['visits'].mean()
    bin_density_means = df_analysis.groupby('density_bin')['population_density'].mean()
    ax1.plot(bin_density_means, bin_means, 'r-o', linewidth=3, markersize=10, label='Bin Means')
    ax1.set_xlabel('Population Density (people/sq mi)')
    ax1.set_ylabel('Visits')
    ax1.set_title('Population Density vs Visits (with Binned Means)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Box plot by bin
    ax2 = axes[0, 1]
    df_analysis.boxplot(column='visits', by='density_bin', ax=ax2)
    ax2.set_xlabel('Population Density Bin')
    ax2.set_ylabel('Visits')
    ax2.set_title('Visit Distribution by Population Density Bin')
    plt.sca(ax2)
    plt.xticks(rotation=45)

    # Plot 3: Competitors by density bin
    ax3 = axes[1, 0]
    bin_competitors = df_analysis.groupby('density_bin')['competitors_5mi'].mean()
    ax3.bar(range(len(bin_competitors)), bin_competitors.values)
    ax3.set_xticks(range(len(bin_competitors)))
    ax3.set_xticklabels(bin_competitors.index, rotation=45)
    ax3.set_xlabel('Population Density Bin')
    ax3.set_ylabel('Average Competitors (5mi)')
    ax3.set_title('Competition Level by Population Density')
    ax3.grid(True, alpha=0.3)

    # Plot 4: Saturation by density bin
    ax4 = axes[1, 1]
    bin_saturation = df_analysis.groupby('density_bin')['saturation_5mi'].mean()
    ax4.bar(range(len(bin_saturation)), bin_saturation.values)
    ax4.set_xticks(range(len(bin_saturation)))
    ax4.set_xticklabels(bin_saturation.index, rotation=45)
    ax4.set_xlabel('Population Density Bin')
    ax4.set_ylabel('Average Saturation (5mi)')
    ax4.set_title('Market Saturation by Population Density')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('data/models/validation_plots/population_density_analysis.png', dpi=300, bbox_inches='tight')
    print("\nVisualization saved to: data/models/validation_plots/population_density_analysis.png")

    return bin_stats


def main():
    """Execute full population density analysis."""
    print("\n" + "="*60)
    print("POPULATION DENSITY ANALYSIS")
    print("Investigating the Population Density Paradox")
    print("="*60 + "\n")

    # Load data
    df = load_data()
    print(f"Training data loaded: {len(df)} dispensaries\n")

    # Analysis 1: Correlation
    correlations = analyze_pop_density_correlation(df)

    # Analysis 2: Non-linear relationship
    nonlinear_results = test_nonlinear_relationship(df)

    # Analysis 3: Competitor confounding
    confounding_results = test_competitor_confounding(df)

    # Analysis 4: Binned analysis with visualization
    bin_stats = create_binned_analysis(df)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY & CONCLUSIONS")
    print("="*60 + "\n")

    print("1. Correlation with Competitors:")
    comp_corr = correlations.get('competitors_5mi', 0)
    print(f"   pop_density ↔ competitors_5mi: {comp_corr:.3f}")
    if comp_corr > 0.5:
        print("   ✅ Strong positive correlation (dense areas have more competitors)")
    else:
        print("   ⚠️  Weak correlation")

    print("\n2. Non-linear Relationship:")
    r2_improvement = nonlinear_results['quadratic_r2'] - nonlinear_results['linear_r2']
    if r2_improvement > 0.01:
        print(f"   ✅ Quadratic model improves R² by {r2_improvement:.4f}")
        print("   Suggests optimal density range exists")
    else:
        print(f"   ⚠️  Quadratic improvement minimal ({r2_improvement:.4f})")
        print("   Linear relationship appears adequate")

    print("\n3. Competitor Confounding:")
    pop_density_alone = confounding_results['Pop Density Only']['coefficients']['population_density']
    pop_density_with_comp = confounding_results['Pop Density + Competitors']['coefficients']['population_density']
    if abs(pop_density_with_comp) < abs(pop_density_alone) * 0.7:
        print("   ✅ Competitor variables explain much of pop_density's negative effect")
        print("   CONCLUSION: Population density paradox is primarily due to competition")
    else:
        print("   ⚠️  Pop_density remains significantly negative even with competitors")
        print("   CONCLUSION: Other factors beyond competition at play")

    print("\n4. Practical Recommendation:")
    if comp_corr > 0.5 and abs(pop_density_with_comp) < abs(pop_density_alone) * 0.7:
        print("   📍 Focus on COMPETITION metrics rather than raw population density")
        print("   📍 Suburban locations with moderate density may outperform dense urban cores")
        print("   📍 The negative pop_density coefficient is NOT inherent to density itself")
    else:
        print("   📍 Population density has independent negative effect beyond competition")
        print("   📍 May reflect market saturation, parking constraints, or demographic factors")

    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
