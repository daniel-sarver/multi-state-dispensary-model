"""
DEPRECATED: This script is no longer needed.

Census tract centroids are now loaded automatically from Gazetteer files
when you first run the coordinate calculator.

The Gazetteer files should already be downloaded. If they're missing,
download them with:

    bash scripts/download_gazetteer_files.sh

Or they will be automatically downloaded on first use of the
coordinate calculator.

---

WHY THIS SCRIPT IS DEPRECATED:

The original plan was to fetch centroids via Census TIGERweb API
(~15-20 minutes for 7,624 tracts). However, Codex review identified
that this approach was too slow and Census Gazetteer files provide
the same authoritative centroids instantly.

Current approach:
- Download Census Gazetteer files once (2.3 MB)
- Extract FL and PA tract centroids (~8,600 tracts total)
- Load centroids automatically from Gazetteer files
- Cache for fast future loading

This is much faster than API calls and provides the same accuracy.
"""

import sys

print("=" * 70)
print("⚠️  DEPRECATED SCRIPT")
print("=" * 70)
print()
print("This script is no longer needed.")
print()
print("Census tract centroids are now loaded automatically from")
print("Census Gazetteer files when you run the coordinate calculator.")
print()
print("If Gazetteer files are missing, download them with:")
print("    bash scripts/download_gazetteer_files.sh")
print()
print("Or they will be downloaded automatically on first use.")
print()
print("=" * 70)

sys.exit(0)
