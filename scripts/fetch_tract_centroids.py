"""
Fetch Census Tract Centroids

One-time script to fetch all FL and PA tract centroids and save to cache.
This takes ~15-20 minutes but only needs to run once.

Run this before using the coordinate calculator for the first time.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feature_engineering.data_loader import MultiStateDataLoader

if __name__ == "__main__":
    print("="*70)
    print("CENSUS TRACT CENTROID FETCHER")
    print("="*70)
    print("\nThis script fetches centroids for all FL and PA census tracts.")
    print("This is a one-time operation that takes ~15-20 minutes.")
    print("Centroids will be cached for future use.\n")

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    print("\nInitializing data loader (this will fetch centroids)...")
    loader = MultiStateDataLoader()

    print("\n" + "="*70)
    print("✅ COMPLETE")
    print("="*70)
    print(f"\nCentroids cached for future use:")
    print(f"  • Florida: {len(loader.fl_census)} tracts")
    print(f"  • Pennsylvania: {len(loader.pa_census)} tracts")
    print(f"\nYou can now use the coordinate calculator without delays.")
