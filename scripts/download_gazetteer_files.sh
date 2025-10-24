#!/bin/bash
# Download Census Gazetteer tract centroid files for FL and PA
#
# These files contain authoritative INTPTLAT/INTPTLONG (internal point lat/lon)
# for every census tract. Used for accurate population/competition calculations.

set -e  # Exit on error

echo "======================================================================"
echo "CENSUS GAZETTEER TRACT CENTROID DOWNLOADER"
echo "======================================================================"
echo ""
echo "Downloading Census Bureau 2020 Gazetteer files for tract centroids..."
echo ""

# Create directory
mkdir -p data/census/gazeteer

# Download national file (contains all states)
echo "📥 Downloading national tract centroids file (2.3 MB)..."
curl -L "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_tracts_national.zip" \
     -o /tmp/2020_Gaz_tracts_national.zip

# Extract
echo "📦 Extracting..."
cd /tmp
unzip -q 2020_Gaz_tracts_national.zip

# Extract FL and PA subsets
echo "🔍 Extracting Florida (12) tracts..."
(head -1 2020_Gaz_tracts_national.txt && awk -F'\t' '$2 ~ /^12/ {print}' 2020_Gaz_tracts_national.txt) \
    > "$OLDPWD/data/census/gazeteer/2020_Gaz_tracts_12.txt"

echo "🔍 Extracting Pennsylvania (42) tracts..."
(head -1 2020_Gaz_tracts_national.txt && awk -F'\t' '$2 ~ /^42/ {print}' 2020_Gaz_tracts_national.txt) \
    > "$OLDPWD/data/census/gazeteer/2020_Gaz_tracts_42.txt"

# Clean up
rm -f 2020_Gaz_tracts_national.txt 2020_Gaz_tracts_national.zip

cd "$OLDPWD"

# Verify
echo ""
echo "======================================================================"
echo "✅ DOWNLOAD COMPLETE"
echo "======================================================================"
echo ""
echo "Files downloaded:"
wc -l data/census/gazeteer/2020_Gaz_tracts_*.txt
echo ""
echo "Expected:"
echo "  • Florida: ~5,160 tracts (5,161 lines with header)"
echo "  • Pennsylvania: ~3,446 tracts (3,447 lines with header)"
echo ""
echo "These centroids will be loaded automatically when you run the"
echo "coordinate calculator. First load will cache them for fast future use."
