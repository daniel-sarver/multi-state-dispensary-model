#!/usr/bin/env python3
"""
Multi-State Dispensary Report Generator

Generates comprehensive HTML, CSV, and TXT reports for site analysis,
modeled on the PA Dispensary Model v3.1 report structure.

Supports both single-site and multi-site analyses for FL and PA.
"""

import json
import base64
import io
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


class ReportGenerator:
    """Generate comprehensive reports for multi-state dispensary analysis."""

    # State-specific branding colors
    STATE_COLORS = {
        'FL': {'primary': '#FF6B35', 'secondary': '#004E89', 'accent': '#F77F00'},  # Florida: Orange/Blue
        'PA': {'primary': '#048A81', 'secondary': '#2E4057', 'accent': '#27AE60'}   # Pennsylvania: Teal/Navy
    }

    def __init__(self, model_info: Dict[str, Any]):
        """
        Initialize report generator.

        Args:
            model_info: Dictionary with model performance metrics and metadata
        """
        self.model_info = model_info
        self.timestamp = datetime.now()

    def generate_reports(
        self,
        results: List[Dict[str, Any]],
        output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Generate all report formats for site analysis.

        Args:
            results: List of site analysis results
            output_dir: Optional custom output directory

        Returns:
            Dictionary mapping report type to file path
        """
        # Create timestamped output directory
        if output_dir is None:
            output_dir = self._create_output_folder()
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Output folder: {output_dir}")
        print("\n📝 Generating reports...")
        print("-" * 50)

        generated_files = {}

        # 1. HTML Report
        html_path = self.generate_html_report(results, output_dir)
        if html_path:
            generated_files['html'] = html_path
            print(f"🌐 HTML Report: {html_path}")

        # 2. CSV Data
        csv_path = self.generate_csv_report(results, output_dir)
        if csv_path:
            generated_files['csv'] = csv_path
            print(f"📊 CSV Data: {csv_path}")

        # 3. Text Summary
        txt_path = self.generate_text_report(results, output_dir)
        if txt_path:
            generated_files['txt'] = txt_path
            print(f"📄 Text Report: {txt_path}")

        # 4. Run Receipt
        receipt_path = self.generate_run_receipt(results, output_dir)
        if receipt_path:
            generated_files['receipt'] = receipt_path
            print(f"📋 Run Receipt: {receipt_path}")

        print(f"\n✅ All reports generated successfully!")
        print(f"   Output folder: {output_dir}")

        return generated_files

    def _create_output_folder(self) -> Path:
        """Create timestamped output folder."""
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        output_dir = Path("site_reports") / f"Site_Analysis_v2_0_{timestamp_str}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def generate_html_report(
        self,
        results: List[Dict[str, Any]],
        output_dir: Path
    ) -> Optional[Path]:
        """
        Generate comprehensive HTML report.

        Modeled on PA Dispensary Model v3.1 report structure with:
        - Summary statistics
        - Performance charts
        - Site rankings table
        - Individual site sections with detailed metrics

        Args:
            results: List of analysis results
            output_dir: Output directory path

        Returns:
            Path to generated HTML file
        """
        if not results:
            print("⚠️ No results to generate HTML report")
            return None

        # Sort results by predicted visits (highest first)
        sorted_results = sorted(
            results,
            key=lambda x: x.get('predicted_visits', 0),
            reverse=True
        )

        # Assign ranks
        for i, result in enumerate(sorted_results, 1):
            result['rank'] = i

        # Determine primary state (most common in results)
        states = [r.get('state', 'FL') for r in results]
        primary_state = max(set(states), key=states.count)
        colors = self.STATE_COLORS.get(primary_state, self.STATE_COLORS['FL'])

        # Create performance chart
        chart_base64 = self._create_performance_chart(sorted_results, primary_state)

        # Generate HTML content
        html_content = self._build_html_content(
            sorted_results, primary_state, colors, chart_base64
        )

        # Write to file
        html_path = output_dir / "analysis_report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return html_path

    def _build_html_content(
        self,
        results: List[Dict[str, Any]],
        primary_state: str,
        colors: Dict[str, str],
        chart_base64: Optional[str]
    ) -> str:
        """Build complete HTML content for report."""
        timestamp_str = self.timestamp.strftime("%B %d, %Y at %I:%M %p")
        best_site = results[0]

        # Get market benchmarks
        state_info = self._get_state_benchmarks(primary_state)

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-State Dispensary Site Analysis Report v2.0</title>
    <style>
        {self._get_css_styles(colors)}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Multi-State Dispensary Site Analysis Report</h1>
            <div class="subtitle">Model v2.0 • Analysis Date: {timestamp_str}</div>
            <div class="subtitle">Primary State: {primary_state}</div>
        </div>

        <div class="summary-section">
            <div class="summary-box">
                <h3>Total Sites Analyzed</h3>
                <div class="value">{len(results)}</div>
                <div class="label">Multi-State Analysis</div>
            </div>
            <div class="summary-box">
                <h3>Best Performing Site</h3>
                <div class="value">{best_site['predicted_visits']:,.0f}</div>
                <div class="label">Site {best_site['rank']} - {best_site['state']}</div>
            </div>
            <div class="summary-box">
                <h3>{primary_state} Market Median</h3>
                <div class="value">{state_info['median_visits']:,.0f}</div>
                <div class="label">Annual Visits (Training Data)</div>
            </div>
        </div>'''

        # Add chart if generated
        if chart_base64:
            html += f'''

        <div class="chart-section">
            <h2>Performance Analysis & Market Comparison</h2>
            <img src="data:image/png;base64,{chart_base64}" alt="Site Performance Comparison"
                 style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        </div>'''

        # Add rankings table
        html += self._build_rankings_table(results)

        # Add individual site sections
        for result in results:
            html += self._build_site_section(result, colors)

        # Add footer
        html += f'''

        <div class="footer">
            <p><strong>Multi-State Dispensary Visit Model v2.0:</strong>
               Test R² = {self.model_info['test_r2']:.4f},
               Cross-Val R² = {self.model_info['cv_r2_mean']:.4f} ± {self.model_info['cv_r2_std']:.4f}</p>
            <p><strong>Training Data:</strong> {self.model_info.get('n_training_samples', 'N/A')} dispensaries
               across Florida and Pennsylvania</p>
            <p><strong>Model Type:</strong> Ridge Regression with state-specific factors and interaction terms</p>
            <p>Report generated: {timestamp_str}</p>
        </div>
    </div>
</body>
</html>'''

        return html

    def _get_css_styles(self, colors: Dict[str, str]) -> str:
        """Get CSS styles with state-specific branding."""
        return f'''
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #ffffff;
            color: #333;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid {colors['primary']};
        }}

        .header h1 {{
            font-size: 24px;
            color: {colors['secondary']};
            margin: 0 0 10px 0;
            font-weight: bold;
        }}

        .header .subtitle {{
            color: #95A5A6;
            font-size: 14px;
        }}

        h2 {{
            color: {colors['secondary']};
            margin-bottom: 20px;
        }}

        .summary-section {{
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
            gap: 20px;
        }}

        .summary-box {{
            flex: 1;
            border: 2px solid {colors['primary']};
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            background-color: rgba(4,138,129,0.1);
        }}

        .summary-box h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            font-weight: bold;
            color: {colors['primary']};
        }}

        .summary-box .value {{
            font-size: 24px;
            font-weight: bold;
            color: {colors['secondary']};
            margin: 10px 0;
        }}

        .summary-box .label {{
            font-size: 12px;
            color: #34495E;
        }}

        .chart-section {{
            margin: 50px 0;
            text-align: center;
        }}

        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .comparison-table th {{
            background-color: {colors['secondary']};
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: bold;
            font-size: 13px;
        }}

        .comparison-table td {{
            padding: 12px;
            border-bottom: 1px solid #ECF0F1;
            font-size: 12px;
        }}

        .comparison-table tr:hover {{
            background-color: rgba(4,138,129,0.05);
        }}

        .comparison-table .site-name {{
            color: {colors['secondary']};
            font-weight: bold;
        }}

        .comparison-table .ranking-cell {{
            text-align: center;
            font-weight: bold;
            color: {colors['secondary']};
        }}

        .individual-site-section {{
            margin: 60px 0;
            padding: 30px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid {colors['primary']};
        }}

        .rank-header {{
            background-color: {colors['primary']};
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 15px;
        }}

        .site-title {{
            color: {colors['secondary']};
            font-size: 18px;
            margin-bottom: 20px;
        }}

        .site-overview {{
            background: white;
            padding: 20px;
            border-radius: 8px;
        }}

        .prediction-box {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['accent']});
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}

        .prediction-box .visits {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}

        .prediction-box .label {{
            font-size: 14px;
            opacity: 0.9;
        }}

        .confidence-box {{
            margin: 10px 0;
            padding: 10px;
            background: rgba(255,255,255,0.2);
            border-radius: 4px;
        }}

        .metrics-row {{
            display: flex;
            justify-content: space-between;
            margin: 30px 0;
            gap: 20px;
        }}

        .metric-box {{
            flex: 1;
            border: 2px solid;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}

        .metric-box.population {{
            border-color: {colors['primary']};
            background-color: rgba(4,138,129,0.1);
        }}

        .metric-box.competition {{
            border-color: #E67E22;
            background-color: rgba(230,126,34,0.1);
        }}

        .metric-box h3 {{
            margin: 0 0 15px 0;
            font-size: 14px;
            font-weight: bold;
        }}

        .metric-box.population h3 {{ color: {colors['primary']}; }}
        .metric-box.competition h3 {{ color: #E67E22; }}

        .metric-item {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 12px;
        }}

        .metric-label {{
            color: #34495E;
        }}

        .metric-value {{
            font-weight: bold;
            color: {colors['secondary']};
        }}

        .confidence-indicator {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            color: white;
        }}

        .confidence-indicator.high {{ background-color: #27AE60; }}
        .confidence-indicator.moderate {{ background-color: #F39C12; }}
        .confidence-indicator.low {{ background-color: #E67E22; }}

        .footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #95A5A6;
            color: #95A5A6;
            font-size: 12px;
        }}
        '''

    def _build_rankings_table(self, results: List[Dict[str, Any]]) -> str:
        """Build HTML rankings table."""
        html = '''

        <div class="comparison-table-section">
            <h2>Site Rankings & Comparison</h2>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>State</th>
                        <th>Coordinates</th>
                        <th>Annual Visits</th>
                        <th>Population (5mi)</th>
                        <th>Competitors (5mi)</th>
                        <th>Square Footage</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>'''

        for result in results:
            conf_level = result.get('confidence_level', 'MODERATE')
            html += f'''
                    <tr>
                        <td class="ranking-cell">#{result['rank']}</td>
                        <td class="site-name">{result.get('state', 'N/A')}</td>
                        <td>{result.get('latitude', 'N/A'):.4f}, {result.get('longitude', 'N/A'):.4f}</td>
                        <td>{result.get('predicted_visits', 0):,.0f}</td>
                        <td>{result.get('pop_5mi', 0):,.0f}</td>
                        <td>{result.get('competitors_5mi', 0)}</td>
                        <td>{result.get('sq_ft', 0):,.0f}</td>
                        <td><span class="confidence-indicator {conf_level.lower()}">{conf_level}</span></td>
                    </tr>'''

        html += '''
                </tbody>
            </table>
        </div>'''

        return html

    def _build_site_section(
        self,
        result: Dict[str, Any],
        colors: Dict[str, str]
    ) -> str:
        """Build individual site detail section."""
        # Calculate confidence level
        ci_range = result.get('ci_upper', 0) - result.get('ci_lower', 0)
        if ci_range < 50000:
            conf_level = "HIGH"
            conf_class = "high"
        elif ci_range < 100000:
            conf_level = "MODERATE"
            conf_class = "moderate"
        else:
            conf_level = "LOW"
            conf_class = "low"

        html = f'''

        <div class="individual-site-section">
            <div class="rank-header">Rank #{result['rank']} - {result.get('state', 'N/A')}</div>
            <h2 class="site-title">Site {result['rank']}: {result.get('latitude', 'N/A'):.6f}, {result.get('longitude', 'N/A'):.6f}</h2>

            <div class="site-overview">
                <div class="prediction-box">
                    <div class="label">Predicted Annual Visits</div>
                    <div class="visits">{result.get('predicted_visits', 0):,.0f}</div>
                    <div class="confidence-box">
                        <div class="label">95% Confidence Interval</div>
                        <div>{result.get('ci_lower', 0):,.0f} - {result.get('ci_upper', 0):,.0f} visits</div>'''

        # Add cap notification if applied
        if result.get('cap_applied', False):
            html += f'''
                        <div style="margin-top: 8px; font-size: 0.85em; color: #666;">
                            ⚠️ Capped at ±{result.get('cap_percentage', 75):.0f}% for usability
                        </div>'''

        html += f'''
                        <div style="margin-top: 10px;">
                            <span class="confidence-indicator {conf_class}">{conf_level} CONFIDENCE</span>
                        </div>
                    </div>
                </div>

                <div class="metrics-row">
                    <div class="metric-box population">
                        <h3>Population Analysis</h3>
                        <div class="metric-item">
                            <span class="metric-label">1 mile radius</span>
                            <span class="metric-value">{result.get('pop_1mi', 0):,.0f}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">3 mile radius</span>
                            <span class="metric-value">{result.get('pop_3mi', 0):,.0f}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">5 mile radius</span>
                            <span class="metric-value">{result.get('pop_5mi', 0):,.0f}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">10 mile radius</span>
                            <span class="metric-value">{result.get('pop_10mi', 0):,.0f}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">20 mile radius</span>
                            <span class="metric-value">{result.get('pop_20mi', 0):,.0f}</span>
                        </div>
                    </div>

                    <div class="metric-box competition">
                        <h3>Competition Analysis</h3>
                        <div class="metric-item">
                            <span class="metric-label">1 mile radius</span>
                            <span class="metric-value">{result.get('competitors_1mi', 0)}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">3 mile radius</span>
                            <span class="metric-value">{result.get('competitors_3mi', 0)}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">5 mile radius</span>
                            <span class="metric-value">{result.get('competitors_5mi', 0)}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">10 mile radius</span>
                            <span class="metric-value">{result.get('competitors_10mi', 0)}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">20 mile radius</span>
                            <span class="metric-value">{result.get('competitors_20mi', 0)}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Distance-weighted (20mi)</span>
                            <span class="metric-value">{result.get('competition_weighted_20mi', 0):.2f}</span>
                        </div>
                    </div>
                </div>

                <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <h3 style="margin-top: 0; color: {colors['secondary']};">Site Demographics</h3>
                    <div class="metrics-row">
                        <div style="flex: 1;">
                            <div class="metric-item">
                                <span class="metric-label">Square Footage</span>
                                <span class="metric-value">{result.get('sq_ft', 0):,.0f} sq ft</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Total Population (tract)</span>
                                <span class="metric-value">{result.get('total_population', 0):,.0f}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Median Age</span>
                                <span class="metric-value">{result.get('median_age', 0):.1f} years</span>
                            </div>
                        </div>
                        <div style="flex: 1;">
                            <div class="metric-item">
                                <span class="metric-label">Median HH Income</span>
                                <span class="metric-value">${result.get('median_household_income', 0):,.0f}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Per Capita Income</span>
                                <span class="metric-value">${result.get('per_capita_income', 0):,.0f}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Population Density</span>
                                <span class="metric-value">{result.get('population_density', 0):,.1f} per sq mi</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>'''

        return html

    def _create_performance_chart(
        self,
        results: List[Dict[str, Any]],
        state: str
    ) -> Optional[str]:
        """Create performance comparison chart as base64 encoded image."""
        try:
            plt.style.use('default')
            fig, ax = plt.subplots(1, 1, figsize=(14, 6))
            fig.suptitle(f'{state} Site Performance Ranking', fontsize=16, fontweight='bold')

            # Prepare data
            sites_data = [r['predicted_visits'] for r in results]
            site_labels = [f"Site {r['rank']}" for r in results]

            # Color scheme
            colors_list = ['#048A81', '#27AE60', '#F39C12', '#E67E22', '#E74C3C',
                          '#9B59B6', '#3498DB', '#1ABC9C', '#F1C40F', '#34495E']
            bar_colors = [colors_list[i % len(colors_list)] for i in range(len(sites_data))]

            # Create horizontal bar chart
            bars = ax.barh(range(len(sites_data)), sites_data, color=bar_colors)

            # Add market median line
            state_info = self._get_state_benchmarks(state)
            median_visits = state_info['median_visits']
            ax.axvline(x=median_visits, color='orange', linestyle='--', linewidth=2,
                      label=f'{state} Market Median ({median_visits:,.0f})')

            ax.set_yticks(range(len(sites_data)))
            ax.set_yticklabels(site_labels)
            ax.set_xlabel('Predicted Annual Visits')
            ax.set_title('Site Performance Comparison')
            ax.legend()
            ax.grid(axis='x', alpha=0.3)

            # Add visit numbers on bars
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 1000, bar.get_y() + bar.get_height()/2,
                       f'{width:,.0f}', ha='left', va='center',
                       fontweight='bold', fontsize=10)

            plt.tight_layout()

            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()

            return chart_base64

        except Exception as e:
            print(f"⚠️  Chart generation failed: {e}")
            return None

    def generate_csv_report(
        self,
        results: List[Dict[str, Any]],
        output_dir: Path
    ) -> Optional[Path]:
        """Generate CSV data export."""
        if not results:
            return None

        # Prepare CSV data
        csv_data = []
        for result in results:
            row = {
                'rank': result.get('rank', 0),
                'state': result.get('state', ''),
                'latitude': result.get('latitude', 0),
                'longitude': result.get('longitude', 0),
                'predicted_annual_visits': result.get('predicted_visits', 0),
                'ci_lower': result.get('ci_lower', 0),
                'ci_upper': result.get('ci_upper', 0),
                'confidence_level': result.get('confidence_level', ''),
                'ci_capped': 'YES' if result.get('cap_applied', False) else 'NO',
                'sq_ft': result.get('sq_ft', 0),
                'pop_1mi': result.get('pop_1mi', 0),
                'pop_3mi': result.get('pop_3mi', 0),
                'pop_5mi': result.get('pop_5mi', 0),
                'pop_10mi': result.get('pop_10mi', 0),
                'pop_20mi': result.get('pop_20mi', 0),
                'competitors_1mi': result.get('competitors_1mi', 0),
                'competitors_3mi': result.get('competitors_3mi', 0),
                'competitors_5mi': result.get('competitors_5mi', 0),
                'competitors_10mi': result.get('competitors_10mi', 0),
                'competitors_20mi': result.get('competitors_20mi', 0),
                'competition_weighted_20mi': result.get('competition_weighted_20mi', 0),
                'median_age': result.get('median_age', 0),
                'median_household_income': result.get('median_household_income', 0),
                'per_capita_income': result.get('per_capita_income', 0),
                'population_density': result.get('population_density', 0),
            }
            csv_data.append(row)

        df = pd.DataFrame(csv_data)
        csv_path = output_dir / "analysis_results.csv"
        df.to_csv(csv_path, index=False)

        return csv_path

    def generate_text_report(
        self,
        results: List[Dict[str, Any]],
        output_dir: Path
    ) -> Optional[Path]:
        """Generate text summary report."""
        timestamp_str = self.timestamp.strftime("%B %d, %Y at %I:%M %p")

        lines = [
            "MULTI-STATE DISPENSARY VISIT MODEL v2.0 - ANALYSIS REPORT",
            "=" * 70,
            f"Analysis Date: {timestamp_str}",
            f"Model Version: v2.0",
            f"Sites Analyzed: {len(results)}",
            f"Test R²: {self.model_info['test_r2']:.4f}",
            f"Cross-Val R²: {self.model_info['cv_r2_mean']:.4f} ± {self.model_info['cv_r2_std']:.4f}",
            "",
            "INDIVIDUAL SITE RESULTS",
            "-" * 70
        ]

        for result in results:
            lines.extend([
                "",
                f"Site {result['rank']}: {result.get('state', 'N/A')}",
                f"  Coordinates: {result.get('latitude', 0):.6f}, {result.get('longitude', 0):.6f}",
                f"  Predicted Annual Visits: {result.get('predicted_visits', 0):,.0f}",
                f"  95% Confidence Interval: {result.get('ci_lower', 0):,.0f} - {result.get('ci_upper', 0):,.0f}" +
                    (" (capped at ±75%)" if result.get('cap_applied', False) else ""),
                f"  Confidence Level: {result.get('confidence_level', 'N/A')}",
                f"  Population (5mi): {result.get('pop_5mi', 0):,.0f}",
                f"  Competitors (5mi): {result.get('competitors_5mi', 0)}"
            ])

        lines.extend([
            "",
            "=" * 70,
            "Multi-State Dispensary Visit Model v2.0",
            "© 2025 INSA Analytics"
        ])

        txt_path = output_dir / "analysis_report.txt"
        with open(txt_path, 'w') as f:
            f.write('\n'.join(lines))

        return txt_path

    def generate_run_receipt(
        self,
        results: List[Dict[str, Any]],
        output_dir: Path
    ) -> Optional[Path]:
        """Generate JSON run receipt with metadata."""
        receipt_data = {
            'analysis_timestamp': self.timestamp.isoformat(),
            'model_version': 'v2.0',
            'model_type': 'Multi-State Ridge Regression',
            'sites_analyzed': len(results),
            'test_r2': self.model_info['test_r2'],
            'cv_r2_mean': self.model_info['cv_r2_mean'],
            'cv_r2_std': self.model_info['cv_r2_std'],
            'states_covered': list(set(r.get('state', 'N/A') for r in results))
        }

        receipt_path = output_dir / "run_receipt.json"
        with open(receipt_path, 'w') as f:
            json.dump(receipt_data, f, indent=2)

        return receipt_path

    def _get_state_benchmarks(self, state: str) -> Dict[str, Any]:
        """Get market benchmarks for state."""
        # These are approximate from the training data
        benchmarks = {
            'FL': {
                'median_visits': 55000,
                'mean_visits': 60000,
                'p25_visits': 35000,
                'p75_visits': 85000
            },
            'PA': {
                'median_visits': 65000,
                'mean_visits': 70000,
                'p25_visits': 45000,
                'p75_visits': 95000
            }
        }
        return benchmarks.get(state, benchmarks['FL'])
