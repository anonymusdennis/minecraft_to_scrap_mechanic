#!/bin/bash
# Fast workflow using on-demand block generation
# This skips the slow pre-generation step

set -e  # Exit on error

echo "==================================="
echo "Minecraft to Scrap Mechanic Converter"
echo "Fast On-Demand Workflow"
echo "==================================="
echo ""

# Configuration
SCHEMATIC_FILE="6901.schematic"
ASSETS_DIR="./MyResourcePack/assets"
OUTPUT_DIR="./assembled_blueprints"
BLUEPRINT_NAME="MyBuilding"

# Step 1: Convert schematic to JSON
echo "Step 1: Converting schematic to JSON..."
if [ -f "$SCHEMATIC_FILE" ]; then
    python3 schematic_to_json.py "$SCHEMATIC_FILE"
    JSON_FILE="${SCHEMATIC_FILE%.schematic}.json"
    echo "✓ Created $JSON_FILE"
else
    echo "✗ Schematic file not found: $SCHEMATIC_FILE"
    echo "  Using existing JSON file if available..."
    JSON_FILE="${SCHEMATIC_FILE%.schematic}.json"
fi
echo ""

# Step 2: Verify assets directory
echo "Step 2: Checking assets directory..."
if [ ! -d "$ASSETS_DIR" ]; then
    echo "✗ Assets directory not found: $ASSETS_DIR"
    echo "  Please extract a Minecraft resource pack to this location."
    exit 1
fi
echo "✓ Assets directory found"
echo ""

# Step 3: Assemble with on-demand generation
echo "Step 3: Assembling schematic with on-demand block generation..."
if [ ! -f "$JSON_FILE" ]; then
    echo "✗ JSON file not found: $JSON_FILE"
    exit 1
fi

python3 schematic_assembler.py "$JSON_FILE" \
    --assets "$ASSETS_DIR" \
    --generate-on-demand \
    --output "$OUTPUT_DIR" \
    --name "$BLUEPRINT_NAME"

echo ""
echo "==================================="
echo "Conversion complete!"
echo "==================================="
echo ""
echo "Your blueprint is ready to use in Scrap Mechanic!"
echo ""
echo "To install:"
echo "1. Open File Explorer and navigate to:"
echo "   %AppData%\\Axolot Games\\Scrap Mechanic\\User\\User_<numbers>\\Blueprints"
echo ""
echo "2. Copy the UUID folder from:"
echo "   $OUTPUT_DIR"
echo ""
echo "3. Launch Scrap Mechanic and find '$BLUEPRINT_NAME' in your blueprints"
echo ""
echo "Note: This workflow uses on-demand block generation, which is much faster"
echo "than pre-generating all blocks. Blocks are generated as needed and cached."
echo ""
