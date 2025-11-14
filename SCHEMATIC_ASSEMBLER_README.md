# Schematic Assembler Tool

This tool creates large voxel-based Scrap Mechanic blueprints from Minecraft schematic files.

## Overview

The schematic assembler takes:
1. A Minecraft schematic file (converted to JSON format)
2. **NEW**: Minecraft assets directory for on-demand block generation, OR
3. **OLD**: A folder of pre-generated block blueprints (created by `main.py`)

And produces:
- A single large, optimized blueprint that recreates the entire Minecraft structure in Scrap Mechanic
- Proper block rotations based on Minecraft data values
- Correct positioning for all blocks
- **Intelligent hollowing** to dramatically reduce file size (enabled by default)

## Usage

### Step 1: Convert Schematic to JSON

If you have a `.schematic` file, first convert it to JSON:

```bash
python3 schematic_to_json.py your_building.schematic
```

This creates `your_building.json`.

### Step 2: Assemble the Blueprint

**Option A: On-Demand Generation (Recommended)**

This is the fastest and simplest approach - blocks are generated as needed:

```bash
python3 schematic_assembler.py your_building.json \
    --assets ./MyResourcePack/assets \
    --generate-on-demand \
    --output ./assembled_blueprints \
    --name "MyBuilding"
```

**Option B: Pre-Generate Block Blueprints**

If you want to pre-generate all block blueprints first:

```bash
# Generate blueprints for all block models
python3 main.py -i ./MyResourcePack/assets -o ./block_blueprints

# Generate additional essential blocks (torches, slabs, glass panes, etc.)
python3 generate_essential_blueprints.py ./MyResourcePack/assets ./block_blueprints

# Assemble using pre-generated blueprints
python3 schematic_assembler.py your_building.json \
    --blueprints ./block_blueprints \
    --output ./assembled_blueprints \
    --name "MyBuilding"
```

**Note**: Hollowing is now **enabled by default** to dramatically reduce file size. Use `--no-hollow` to disable if needed (not recommended).

### Arguments

- `schematic`: Path to the Minecraft schematic JSON file (required)
- `--blueprints` / `-b`: Path to folder containing pre-generated block blueprints (required unless using `--generate-on-demand`)
- `--assets` / `-a`: Path to Minecraft assets directory (e.g., `./MyResourcePack/assets`) for on-demand generation
- `--generate-on-demand`: Generate block blueprints on-demand instead of using pre-generated blueprints. Requires `--assets`. **Recommended for faster workflow**
- `--output` / `-o`: Output directory for assembled blueprint (default: `./assembled_blueprints`)
- `--name` / `-n`: Name for the blueprint (default: `MinecraftSchematic`)
- `--hollow`: Hollow out the blueprint to remove interior voxels. **This is now the default behavior**
- `--no-hollow`: Disable hollowing (not recommended - will result in much larger files)

## Example

**Recommended: On-Demand Generation**

```bash
# Convert schematic
python3 schematic_to_json.py 6901.schematic

# Assemble with on-demand generation (no pre-generation needed!)
python3 schematic_assembler.py 6901.json \
    --assets ./MyResourcePack/assets \
    --generate-on-demand \
    -o ./my_builds \
    -n "Medieval_Castle"
```

**Alternative: Pre-Generated Blueprints**

```bash
# Convert schematic
python3 schematic_to_json.py 6901.schematic

# Generate block blueprints (do both steps for best coverage)
python3 main.py -i ./MyResourcePack/assets -o ./block_blueprints
python3 generate_essential_blueprints.py ./MyResourcePack/assets ./block_blueprints

# Assemble large blueprint
python3 schematic_assembler.py 6901.json \
    -b ./block_blueprints \
    -o ./my_builds \
    -n "Medieval_Castle"
```

## How It Works

### Intelligent Hollowing (Default Optimization)

**NEW**: Hollowing is now **enabled by default** and uses a smarter algorithm that:
- Builds the complete structure internally with solid blocks
- Uses BFS to calculate distance from surface for each voxel
- Keeps only voxels within distance 1 of the surface (1-2 voxel thick walls)
- Verifies connectivity to prevent floating parts
- **Reduces file size by 95-98%** for typical structures

Benefits:
- **Dramatically reduces file size** (e.g., 1.5GB → 31MB in testing)
- **Prevents crashes** when loading huge blueprints in Scrap Mechanic
- **Improves game performance** significantly
- **Keeps visual appearance identical** (only the outer shell is visible anyway)
- **Maintains structural integrity** (no floating parts)

Example voxel count reductions:
- 20x20x20 cube: 8,000 → 3,904 voxels (51% reduction)
- 25x39x35 house: 16.8M → 218K voxels (98.7% reduction)

**Note**: Use `--no-hollow` only if you specifically need all interior voxels (not recommended).

### Preview Images

The assembler automatically generates a preview image (`icon.png`) for your blueprint, showing an isometric view of the structure. This appears in Scrap Mechanic's blueprint selection screen.

### Block Matching

The tool tries to match Minecraft blocks to generated blueprints using:
- Direct name matching (e.g., "oak_planks" → "oak_planks")
- Partial matching (e.g., "stone_slab" → "stone")
- Material/type extraction (e.g., "oak_planks" → "oak" or "planks")

### Rotation Handling

The tool determines proper rotation for directional blocks based on Minecraft data values:

- **Stairs**: Uses bits 0-1 for direction (north/south/east/west), bit 2 for upside-down
- **Logs**: Uses bits 2-3 for orientation (vertical/east-west/north-south)
- **Slabs**: Uses bit 3 for top/bottom half
- **Torches/Buttons/Levers**: Uses data value for wall mounting direction
- **Doors/Gates**: Uses bits 0-1 for hinge direction

### Coordinate Conversion

Minecraft and Scrap Mechanic use different coordinate systems:
- **Minecraft**: X=east, Y=up, Z=south
- **Scrap Mechanic**: X=right, Y=forward, Z=up

The tool automatically converts between these systems.

## Limitations

### Missing Blueprints

Not all Minecraft blocks have corresponding generated blueprints. When a block is missing:
- A default gray cube is used as a fallback
- The missing block name is reported in the output statistics

To minimize missing blocks, ensure you:
1. Use a complete Minecraft resource pack
2. Generate blueprints for all block models

### Complex Rotations

Some complex block rotations (like heads, banners, or rotated logs) may not be perfectly represented due to differences between Minecraft and Scrap Mechanic rotation systems.

### Scale

Large schematics create very large blueprints that may be difficult to load or use in Scrap Mechanic. Consider:
- Breaking large structures into smaller sections
- Simplifying complex structures before conversion

## Output Format

The assembled blueprint is saved in Scrap Mechanic's standard format:

```
output_folder/
  └── <UUID>/
      ├── blueprint.json    # Contains all voxel data
      ├── description.json  # Blueprint metadata
      └── icon.png          # Preview image (generated automatically)
```

To use in Scrap Mechanic:
1. Copy the UUID folder to your Scrap Mechanic blueprints directory:
   ```
   %AppData%\Axolot Games\Scrap Mechanic\User\User_<id>\Blueprints\
   ```
2. Launch Scrap Mechanic
3. Open the Lift and select your blueprint from the list

## Troubleshooting

### "Blueprint folder not found"
- Make sure you've run `main.py` first to generate block blueprints
- Check that the path to blueprints folder is correct

### "Missing blueprints" warnings
- This is normal - not all Minecraft blocks have models
- Gray cubes are used as fallbacks for missing blocks
- To improve coverage, use a more complete resource pack

### Blueprint is too large or crashes the game
- **NEW**: Hollowing is now **enabled by default** and provides 95-98% file size reduction
- If you disabled hollowing with `--no-hollow`, remove that flag to enable the optimization
- The intelligent hollowing algorithm keeps only the outer shell (1-2 voxels thick), which is all that's visible
- If the structure is still too large even with hollowing, consider splitting your schematic into smaller sections
- Use WorldEdit or similar tools to divide large structures

### Incorrect rotations
- Some block types may have limited rotation support
- Report issues with specific block types for improvement

## Advanced Usage

### Batch Processing

Process multiple schematics at once:

```bash
for schematic in *.json; do
    name=$(basename "$schematic" .json)
    python3 schematic_assembler.py "$schematic" \
        -b ./block_blueprints \
        -o ./assembled_blueprints \
        -n "$name"
done
```

### Custom Block Mapping

To add support for custom blocks or improve matching, edit:
- `block_ids.py`: Add block ID mappings
- `schematic_assembler.py`: Modify `determine_rotation()` for custom rotation logic
- `schematic_assembler.py`: Update `load_blueprint_blocks()` for better matching

## Contributing

To improve block support:
1. Add new block IDs to `block_ids.py`
2. Implement rotation logic in `determine_rotation()`
3. Test with various schematic files
4. Submit improvements via pull request
