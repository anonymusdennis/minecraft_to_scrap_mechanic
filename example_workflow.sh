#!/bin/bash
# Example workflow for converting a Minecraft schematic to Scrap Mechanic blueprint

set -e  # Exit on error

echo "==================================="
echo "Minecraft to Scrap Mechanic Converter"
echo "==================================="
echo ""

# Configuration
SCHEMATIC_FILE="6901.schematic"
ASSETS_DIR="./MyResourcePack/assets"
BLUEPRINTS_DIR="./generated_blueprints"
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

# Step 2: Generate block blueprints
echo "Step 2: Generating block blueprints..."
if [ ! -d "$ASSETS_DIR" ]; then
    echo "✗ Assets directory not found: $ASSETS_DIR"
    echo "  Please extract a Minecraft resource pack to this location."
    exit 1
fi

echo "  Generating main blueprints..."
python3 main.py -i "$ASSETS_DIR" -o "$BLUEPRINTS_DIR"

echo "  Generating essential blocks..."
python3 generate_essential_blueprints.py "$ASSETS_DIR" "$BLUEPRINTS_DIR"

BLUEPRINT_COUNT=$(ls -1 "$BLUEPRINTS_DIR" | wc -l)
echo "✓ Generated $BLUEPRINT_COUNT blueprints"
echo ""

# Step 3: Assemble the large blueprint
echo "Step 3: Assembling schematic into large blueprint..."
if [ ! -f "$JSON_FILE" ]; then
    echo "✗ JSON file not found: $JSON_FILE"
    exit 1
fi

python3 schematic_assembler.py "$JSON_FILE" \
    --blueprints "$BLUEPRINTS_DIR" \
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
