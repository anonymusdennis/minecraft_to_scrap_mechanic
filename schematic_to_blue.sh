#!/bin/bash
# ===================================
# Quick Schematic to Blueprint Converter
# Usage: schematic_to_blue.sh <schematic_file>
# ===================================

set -e  # Exit on error

if [ -z "$1" ]; then
    echo "Usage: schematic_to_blue.sh <schematic_file>"
    echo "Example: schematic_to_blue.sh 6901.schematic"
    exit 1
fi

SCHEMATIC_FILE="$1"
ASSETS_DIR="./MyResourcePack/assets"
OUTPUT_DIR="./assembled_blueprints"

# Extract filename without extension for blueprint name
BLUEPRINT_NAME=$(basename "$SCHEMATIC_FILE" .schematic)

echo "==================================="
echo "Converting: $SCHEMATIC_FILE"
echo "==================================="
echo ""

# Check if schematic file exists
if [ ! -f "$SCHEMATIC_FILE" ]; then
    echo "Error: Schematic file not found: $SCHEMATIC_FILE"
    exit 1
fi

# Check if assets directory exists
if [ ! -d "$ASSETS_DIR" ]; then
    echo "Error: Assets directory not found: $ASSETS_DIR"
    echo "Please extract a Minecraft resource pack to $ASSETS_DIR"
    exit 1
fi

# Step 1: Convert schematic to JSON
echo "[1/2] Converting schematic to JSON..."
python3 schematic_to_json.py "$SCHEMATIC_FILE"

JSON_FILE="${SCHEMATIC_FILE%.schematic}.json"
echo "✓ Created $JSON_FILE"
echo ""

# Step 2: Assemble blueprint with on-demand generation
echo "[2/2] Assembling blueprint with on-demand generation..."
# Add --split flag for large builds (comment out if not needed)
python3 schematic_assembler.py "$JSON_FILE" \
    --assets "$ASSETS_DIR" \
    --generate-on-demand \
    --output "$OUTPUT_DIR" \
    --name "$BLUEPRINT_NAME"
    # --split \
    # --max-voxels-per-chunk 50000

echo ""
echo "==================================="
echo "Success!"
echo "==================================="
echo ""
echo "Blueprint saved to: $OUTPUT_DIR"
echo "Blueprint name: $BLUEPRINT_NAME"
echo ""
echo "To install in Scrap Mechanic:"
echo "1. Copy the UUID folder from $OUTPUT_DIR to:"
echo "   %AppData%\\Axolot Games\\Scrap Mechanic\\User\\User_<numbers>\\Blueprints"
echo ""
echo "2. Launch Scrap Mechanic and find '$BLUEPRINT_NAME' in your blueprints"
echo ""
echo "NOTE: For very large builds, edit this script to uncomment --split flag"
echo "      This will automatically divide the blueprint into manageable chunks"
echo ""
