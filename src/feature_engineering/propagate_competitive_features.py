"""
Propagate competitive features from combined dataset back to state-specific files.

This ensures downstream scripts can use either:
1. State-specific files (FL_combined_dataset_current.csv, PA_combined_dataset_current.csv)
2. Combined file (combined_with_competitive_features.csv)

Both will have the same schema including all Phase 3 competitive features.

Part of Phase 3: Model Development
Multi-State Dispensary Prediction Model
"""

import pandas as pd
import logging
import json
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def propagate_features():
    """
    Propagate competitive features from combined dataset to state files.
    """
    logger.info("="*80)
    logger.info("PROPAGATING COMPETITIVE FEATURES TO STATE FILES")
    logger.info("="*80)

    # Load combined dataset with competitive features
    combined_path = 'data/processed/combined_with_competitive_features.csv'
    logger.info(f"Loading combined dataset: {combined_path}")
    combined_df = pd.read_csv(combined_path)

    logger.info(f"Combined dataset: {len(combined_df)} rows, {len(combined_df.columns)} columns")

    # Identify competitive feature columns
    comp_features = [col for col in combined_df.columns if any(x in col for x in [
        'competitor', 'saturation', 'affluent', 'educated', 'age_adjusted', 'competition_weighted'
    ])]

    logger.info(f"\nCompetitive features to propagate: {len(comp_features)}")
    for feat in sorted(comp_features):
        logger.info(f"  - {feat}")

    # Split back to state-specific datasets
    fl_df = combined_df[combined_df['state'] == 'FL'].copy()
    pa_df = combined_df[combined_df['state'] == 'PA'].copy()

    logger.info(f"\nSplit datasets:")
    logger.info(f"  FL: {len(fl_df)} rows, {len(fl_df.columns)} columns")
    logger.info(f"  PA: {len(pa_df)} rows, {len(pa_df.columns)} columns")

    # Backup original files
    fl_original = 'data/processed/FL_combined_dataset_current.csv'
    pa_original = 'data/processed/PA_combined_dataset_current.csv'

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    fl_backup = f'data/processed/archive/FL_combined_dataset_{timestamp}_pre_phase3.csv'
    pa_backup = f'data/processed/archive/PA_combined_dataset_{timestamp}_pre_phase3.csv'

    # Create archive directory if needed
    Path('data/processed/archive').mkdir(parents=True, exist_ok=True)

    logger.info(f"\nCreating backups:")
    logger.info(f"  FL: {fl_backup}")
    logger.info(f"  PA: {pa_backup}")

    # Backup original files
    pd.read_csv(fl_original).to_csv(fl_backup, index=False)
    pd.read_csv(pa_original).to_csv(pa_backup, index=False)

    # Save updated files with competitive features
    logger.info(f"\nSaving updated state files:")
    logger.info(f"  FL: {fl_original}")
    logger.info(f"  PA: {pa_original}")

    fl_df.to_csv(fl_original, index=False)
    pa_df.to_csv(pa_original, index=False)

    # Create update report
    report = {
        'timestamp': datetime.now().isoformat(),
        'phase': 'Phase 3: Competitive Features',
        'source_file': combined_path,
        'competitive_features_added': comp_features,
        'num_features_added': len(comp_features),
        'florida': {
            'file': fl_original,
            'backup': fl_backup,
            'rows': len(fl_df),
            'columns': len(fl_df.columns),
            'training_rows': int(fl_df['has_placer_data'].sum()),
            'regulator_only_rows': int((~fl_df['has_placer_data']).sum())
        },
        'pennsylvania': {
            'file': pa_original,
            'backup': pa_backup,
            'rows': len(pa_df),
            'columns': len(pa_df.columns),
            'training_rows': int(pa_df['has_placer_data'].sum()),
            'regulator_only_rows': int((~pa_df['has_placer_data']).sum())
        },
        'data_quality': {
            'fl_competitive_features_complete': int(fl_df[fl_df['has_placer_data']][comp_features[0]].notna().sum()),
            'pa_competitive_features_complete': int(pa_df[pa_df['has_placer_data']][comp_features[0]].notna().sum()),
            'fl_training_total': int(fl_df['has_placer_data'].sum()),
            'pa_training_total': int(pa_df['has_placer_data'].sum())
        }
    }

    report_path = 'data/processed/competitive_features_propagation_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nReport saved: {report_path}")

    logger.info("\n" + "="*80)
    logger.info("PROPAGATION COMPLETE")
    logger.info("="*80)
    logger.info(f"State files updated with {len(comp_features)} competitive features")
    logger.info(f"Original files backed up with timestamp: {timestamp}")
    logger.info("\nDownstream scripts can now use:")
    logger.info(f"  1. State files: {fl_original}, {pa_original}")
    logger.info(f"  2. Combined file: {combined_path}")
    logger.info("All files have identical schemas including Phase 3 features.")


if __name__ == '__main__':
    propagate_features()
