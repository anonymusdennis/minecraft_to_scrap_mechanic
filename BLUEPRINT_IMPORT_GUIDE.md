# Blueprint Import Guide

This guide helps troubleshoot blueprint import issues in Scrap Mechanic and explains alternative methods for importing your Minecraft structures.

## Table of Contents

1. [Common Issues & Solutions](#common-issues--solutions)
2. [Blueprint Splitting Feature](#blueprint-splitting-feature)
3. [Installation Methods](#installation-methods)
4. [Troubleshooting](#troubleshooting)
5. [Technical Details](#technical-details)

---

## Common Issues & Solutions

### Issue: "Cannot paste blueprint into the world"

This is typically caused by one of the following:

#### 1. **Blueprint Too Large**
Scrap Mechanic has limits on blueprint complexity. Very large structures (100,000+ voxels) may fail to place.

**Solution:** Use the new **`--split`** option to automatically divide your blueprint into manageable chunks:

```bash
python3 schematic_assembler.py my_building.json \
    --assets ./MyResourcePack/assets \
    --generate-on-demand \
    --split \
    --max-voxels-per-chunk 50000 \
    -o ./output \
    -n "MyBuilding"
```

This creates multiple smaller blueprints that you can place individually and assemble in-game.

#### 2. **Game Performance**
Your computer may not have enough resources to handle the blueprint.

**Solutions:**
- Lower graphics settings in Scrap Mechanic
- Close other programs
- Use the `--split` option to create smaller blueprints
- Ensure hollowing is enabled (it's on by default)

#### 3. **File Corruption**
The blueprint file may be corrupted or improperly formatted.

**Solution:** 
- Re-run the conversion with the latest version of the tool
- Check that the JSON files are valid
- Verify files are not empty or truncated

#### 4. **Invalid Placement Location**
You might be trying to place the blueprint in an invalid location (e.g., overlapping with existing structures or terrain).

**Solutions:**
- Try placing in an empty area
- Clear the area first
- Use Creative Mode for easier placement

---

## Blueprint Splitting Feature

### Overview

The new `--split` option automatically divides large structures into multiple smaller blueprints after hollowing. This makes massive builds manageable in Scrap Mechanic.

### How It Works

1. **Assembles** the complete structure from your schematic
2. **Hollows out** interior voxels to reduce size
3. **Analyzes** the structure's size and complexity
4. **Splits** into spatial chunks if it exceeds the threshold
5. **Generates** multiple blueprint files, each under the size limit

### Usage Examples

#### Automatic Splitting (Recommended)

```bash
# Let the tool automatically determine chunk size
python3 schematic_assembler.py castle.json \
    --assets ./MyResourcePack/assets \
    --generate-on-demand \
    --split \
    -o ./output \
    -n "Medieval_Castle"
```

#### Custom Chunk Size

```bash
# Specify maximum voxels per chunk (default is 50,000)
python3 schematic_assembler.py huge_city.json \
    --assets ./MyResourcePack/assets \
    --generate-on-demand \
    --split \
    --max-voxels-per-chunk 30000 \
    -o ./output \
    -n "City"
```

#### Quick Script

Use the convenience scripts with splitting enabled:

**Windows:**
```batch
REM Edit schematic_to_blue.bat and add --split flag
python schematic_assembler.py "%JSON_FILE%" ^
    --assets "%ASSETS_DIR%" ^
    --generate-on-demand ^
    --split ^
    --output "%OUTPUT_DIR%" ^
    --name "%BLUEPRINT_NAME%"
```

**Linux/Mac:**
```bash
# Edit schematic_to_blue.sh and add --split flag
python3 schematic_assembler.py "$JSON_FILE" \
    --assets "$ASSETS_DIR" \
    --generate-on-demand \
    --split \
    --output "$OUTPUT_DIR" \
    --name "$BLUEPRINT_NAME"
```

### Output Format

When splitting is enabled and multiple chunks are created:

```
output_folder/
├── <UUID-1>/
│   ├── blueprint.json
│   ├── description.json
│   └── icon.png
├── <UUID-2>/
│   ├── blueprint.json
│   ├── description.json
│   └── icon.png
└── <UUID-3>/
    ├── blueprint.json
    ├── description.json
    └── icon.png
```

Each chunk is named: `YourBuildingName_part_1_of_3`, `YourBuildingName_part_2_of_3`, etc.

### Assembling Split Blueprints In-Game

1. **Copy all chunk folders** to your Scrap Mechanic Blueprints directory:
   ```
   %AppData%\Axolot Games\Scrap Mechanic\User\User_<numbers>\Blueprints\
   ```

2. **Launch Scrap Mechanic** and open the Lift

3. **Place each chunk** in order:
   - Start with `part_1_of_X`
   - Carefully align `part_2_of_X` next to it
   - Continue until all parts are placed
   - The chunks are designed to fit together spatially

4. **Tips for alignment:**
   - Use grid mode (press G) for precise placement
   - Zoom in close to see alignment
   - Place on a flat surface first, then lift if needed
   - Consider using wedges or blocks as alignment guides

---

## Installation Methods

### Method 1: Blueprint Library (Standard)

This is the standard method that works for most blueprints:

1. **Generate your blueprint:**
   ```bash
   python3 schematic_to_json.py my_building.schematic
   python3 schematic_assembler.py my_building.json \
       --assets ./MyResourcePack/assets \
       --generate-on-demand \
       -o ./output \
       -n "MyBuilding"
   ```

2. **Locate the output folder** (e.g., `./output/<UUID>/`)

3. **Copy to Scrap Mechanic:**
   - Windows: `%AppData%\Axolot Games\Scrap Mechanic\User\User_<numbers>\Blueprints\`
   - Linux: `~/.local/share/Axolot Games/Scrap Mechanic/User/User_<numbers>/Blueprints/`

4. **Find the UUID folder** with your schematic name and copy it

5. **Launch Scrap Mechanic**, open the Lift, and find your blueprint

### Method 2: Using Blueprint Splitting (For Large Builds)

Follow Method 1 but add the `--split` flag. See [Blueprint Splitting Feature](#blueprint-splitting-feature) above.

### Method 3: Direct World Insertion (Not Currently Supported)

**Note:** This feature is **not currently implemented** but is being researched.

Scrap Mechanic world files use a proprietary format:
- Located at: `%AppData%\Axolot Games\Scrap Mechanic\User\User_<numbers>\Save\Survival\<world_name>\`
- Key files: `world.db`, `terrain.db`, `tile_*.json`
- Format is complex and undocumented

**Potential future features:**
- Direct injection into world save files
- Placing structures without using the Lift
- Pre-building structures in specific coordinates

If you need this feature, please:
1. Check for updates to this tool
2. Look for community mods that support world editing
3. Consider using the blueprint splitting method as an alternative

---

## Troubleshooting

### "Blueprint doesn't appear in the Lift"

**Possible causes:**
- Files copied to wrong directory
- Description.json is malformed
- Game needs to be restarted

**Solutions:**
1. Verify you copied to the correct `Blueprints` folder
2. Check that folder contains `blueprint.json`, `description.json`, and `icon.png`
3. Completely exit and restart Scrap Mechanic
4. Check the description.json file is valid JSON

### "Blueprint appears but crashes when trying to place"

**Possible causes:**
- Too many voxels
- Overlapping parts
- Invalid rotation values

**Solutions:**
1. Use the `--split` option to create smaller chunks
2. Ensure hollowing is enabled (default)
3. Regenerate the blueprint from scratch
4. Try with `--max-voxels-per-chunk 30000` for smaller chunks

### "Parts are missing or wrong colors"

**Possible causes:**
- Missing block blueprints
- Incomplete resource pack
- Texture sampling issues

**Solutions:**
1. Use a complete Minecraft resource pack
2. Check the console output for "missing blueprints"
3. Re-run with `--generate-on-demand` for better coverage

### "Chunks don't align properly"

**Possible causes:**
- Floating point precision
- Incorrect placement order
- Gaps in splitting algorithm

**Solutions:**
1. Use grid mode (G key) in Scrap Mechanic
2. Place on a flat surface first
3. Zoom in close for precise alignment
4. Try adjusting `--max-voxels-per-chunk` to change chunk boundaries

### "Out of memory error during generation"

**Possible causes:**
- Extremely large schematic
- Insufficient RAM
- Too many processes running

**Solutions:**
1. Close other programs
2. Use a smaller schematic or split it beforehand using WorldEdit
3. Increase swap space on Linux
4. Try processing on a machine with more RAM

---

## Technical Details

### Blueprint Format

Scrap Mechanic blueprints use JSON format:

```json
{
  "bodies": [{
    "childs": [
      {
        "bounds": {"x": 1, "y": 1, "z": 1},
        "color": "FF0000",
        "pos": {"x": 0, "y": 0, "z": 0},
        "shapeId": "628b2d61-5ceb-43e9-8334-a4135566df7a",
        "xaxis": 1,
        "zaxis": 3
      }
    ]
  }],
  "version": 4
}
```

### Size Limits

Based on testing and community feedback:

| Voxel Count | Placement Success | Performance |
|-------------|-------------------|-------------|
| < 10,000    | ✅ Excellent      | Smooth      |
| 10,000-50,000 | ✅ Good         | Minor lag   |
| 50,000-100,000 | ⚠️ Possible    | Laggy       |
| 100,000-200,000 | ⚠️ Difficult  | Very laggy  |
| > 200,000   | ❌ Usually fails | Crashes     |

**Recommendation:** Use `--split` with `--max-voxels-per-chunk 50000` for builds over 50,000 voxels.

### Chunk Splitting Algorithm

1. **Calculate bounding box** of all voxels
2. **Determine chunk grid** based on max voxels per chunk
3. **Assign each voxel** to a chunk based on its position
4. **Create separate blueprints** for each chunk
5. **Name sequentially** for easy assembly

The algorithm tries to create roughly cubic chunks rather than thin slices.

### Hollowing Algorithm

Before splitting, the blueprint is hollowed:

1. **Build position map** of all voxels
2. **Find surface voxels** (those with at least one empty neighbor)
3. **BFS distance calculation** from surface
4. **Keep voxels** within distance 1 of surface
5. **Result:** 1-2 voxel thick walls, 95-98% size reduction

### Coordinate Systems

**Minecraft:**
- X = East/West
- Y = Up/Down
- Z = North/South

**Scrap Mechanic:**
- X = Right/Left
- Y = Forward/Back
- Z = Up/Down

**Conversion:**
- MC X → SM X
- MC Y → SM Z
- MC Z → SM Y

---

## Advanced Usage

### Batch Processing with Splitting

Process multiple schematics with automatic splitting:

```bash
for schematic in *.schematic; do
    name=$(basename "$schematic" .schematic)
    python3 schematic_to_json.py "$schematic"
    python3 schematic_assembler.py "${schematic%.schematic}.json" \
        --assets ./MyResourcePack/assets \
        --generate-on-demand \
        --split \
        --max-voxels-per-chunk 40000 \
        -o ./output \
        -n "$name"
done
```

### Custom Chunk Strategy

For specific building layouts (e.g., skyscrapers), you might want vertical splits:

```python
# Future feature - not yet implemented
# This would be added to schematic_assembler.py
python3 schematic_assembler.py building.json \
    --split \
    --split-strategy vertical \
    --floors-per-chunk 10
```

### Pre-splitting in Minecraft

For extremely large structures, consider splitting in Minecraft first:

1. Use WorldEdit or similar
2. Select portions of your structure
3. Save as separate schematics
4. Convert each separately
5. Place in Scrap Mechanic with proper spacing

---

## Contributing

Found a bug or have a suggestion? Please:

1. Check existing issues on GitHub
2. Provide your schematic file (if possible)
3. Include error messages and logs
4. Describe your system specs

## Future Improvements

Planned features:

- [ ] Direct world file injection
- [ ] GUI for blueprint management
- [ ] Automatic alignment of split chunks in-game
- [ ] Custom splitting strategies (vertical, horizontal, etc.)
- [ ] Blueprint preview before placement
- [ ] LOD (Level of Detail) system for very large structures
- [ ] Integration with Scrap Mechanic Workshop

---

## FAQ

**Q: Can I modify blueprints after generation?**
A: Yes, the JSON files can be edited manually, but be careful with the format.

**Q: Why does my blueprint look different from Minecraft?**
A: Scrap Mechanic's voxel system and materials differ from Minecraft. Some approximation is necessary.

**Q: Can I use custom Minecraft blocks?**
A: Yes, if you have a resource pack with their models. Use `--generate-on-demand` with `--assets`.

**Q: How do I know if I need to split?**
A: If your blueprint has more than 50,000 voxels after hollowing, or if placement fails, use `--split`.

**Q: Can I adjust chunk size after generation?**
A: You need to re-run the assembler with a different `--max-voxels-per-chunk` value.

**Q: Do I need all chunks to use the blueprint?**
A: Each chunk is a complete, standalone blueprint. You can use any subset, but the full structure requires all chunks.

---

**Last Updated:** 2025-11-14
**Tool Version:** Compatible with latest schematic_assembler.py
