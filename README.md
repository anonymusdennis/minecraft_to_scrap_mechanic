# Minecraft to Scrap Mechanic Converter

Convert Minecraft structures and schematics into Scrap Mechanic blueprints!

## Features

- **Block Model Converter**: Convert individual Minecraft block models to Scrap Mechanic blueprints
- **Schematic Assembler**: Convert entire Minecraft schematics into large voxel-based Scrap Mechanic blueprints
- **Rotation Support**: Properly handles directional blocks (stairs, logs, torches, etc.)
- **Material Mapping**: Maps Minecraft blocks to appropriate Scrap Mechanic materials
- **Preview Images**: Generates preview icons for blueprints

## Quick Start

### Prerequisites

```bash
pip install Pillow
```

### Basic Workflow

1. **Convert Minecraft block models to blueprints:**
   ```bash
   python3 main.py -i ./MyResourcePack/assets -o ./blueprints
   python3 generate_essential_blueprints.py ./MyResourcePack/assets ./blueprints
   ```

2. **Convert a schematic file:**
   ```bash
   python3 schematic_to_json.py my_building.schematic
   ```

3. **Assemble the large blueprint:**
   ```bash
   python3 schematic_assembler.py my_building.json \
       -b ./blueprints \
       -o ./output \
       -n "MyBuilding"
   ```

4. **Install in Scrap Mechanic:**
   - Copy the generated UUID folder from `./output` to:
     ```
     %AppData%\Axolot Games\Scrap Mechanic\User\User_<numbers>\Blueprints\
     ```
   
5. **For Large Builds:** Use the `--split` option to automatically divide into manageable chunks:
   ```bash
   python3 schematic_assembler.py my_building.json \
       --assets ./MyResourcePack/assets \
       --generate-on-demand \
       --split \
       -o ./output \
       -n "MyBuilding"
   ```
   See [Blueprint Import Guide](BLUEPRINT_IMPORT_GUIDE.md) for details.

### Quick Start - Single Command

The fastest way to convert a schematic:

**Windows:**
```bash
schematic_to_blue.bat my_building.schematic
```

**Linux/Mac:**
```bash
./schematic_to_blue.sh my_building.schematic
```

This script automatically:
- Converts the schematic to JSON
- Generates blocks on-demand
- Creates an optimized, hollowed blueprint
- Uses default folders (`./MyResourcePack/assets`, `./assembled_blueprints`)

### Manual Workflow (More Control)

If you need more control over the process:

```bash
# 1. Convert schematic to JSON
python3 schematic_to_json.py my_building.schematic

# 2. (Recommended) Generate essential blueprints for special blocks
#    These include entity blocks (chest, bed), thin blocks (glass, iron_bars),
#    and multi-part blocks (doors, trapdoors, snow layers, bells, scaffolding)
python3 generate_essential_blueprints.py ./MyResourcePack/assets ./blueprints

# 3. Assemble with hybrid approach (pre-generated + on-demand)
#    Uses pre-generated blueprints first, then generates on-demand if needed
python3 schematic_assembler.py my_building.json \
    -b ./blueprints \
    --assets ./MyResourcePack/assets \
    --generate-on-demand \
    -o ./output \
    -n "MyBuilding"
```

### Automated Workflow

Use the example workflow script:

```bash
bash example_workflow.sh
```

## Tools

### 1. `main.py` - Block Model Converter

Converts Minecraft block models (JSON) to Scrap Mechanic blueprints.

```bash
python3 main.py -i <assets_dir> -o <output_dir>
```

### 2. `generate_essential_blueprints.py` - Essential Blocks Generator

Generates commonly-used blocks that might be missed by main.py or are special cases:
- **Entity blocks**: chest, bed (blocks that use entity models in Minecraft)
- **Thin geometry blocks**: glass, iron_bars (blocks with very thin elements that don't voxelize well)
- **Multi-part blocks**: doors, trapdoors, snow layers, bells, scaffolding
- **Stained glass panes**: All 16 color variants

```bash
python3 generate_essential_blueprints.py <assets_dir> <output_dir>
```

### 3. `schematic_to_json.py` - Schematic Converter

Converts Minecraft .schematic files (NBT format) to JSON.

```bash
python3 schematic_to_json.py <input.schematic> [output.json]
```

**Note**: This tool handles the old WorldEdit format (.schematic files). For newer WorldEdit Version 3+ format (.schem files), you can convert them to JSON manually or use them directly if already in JSON format.

### 4. `schematic_assembler.py` - Schematic Assembler

Assembles a large Scrap Mechanic blueprint from a Minecraft schematic. Supports both old (pre-1.13) and new WorldEdit Version 3+ schematic formats.

**New: On-Demand Generation** (Recommended)
```bash
python3 schematic_assembler.py <schematic.json> \
    --assets <assets_dir> \
    --generate-on-demand \
    -o <output_dir> \
    -n <name>
```

**Traditional: Using Pre-Generated Blueprints**
```bash
python3 schematic_assembler.py <schematic.json> \
    -b <blueprints_dir> \
    -o <output_dir> \
    -n <name>
```

## Documentation

- [Blueprint Import Guide](BLUEPRINT_IMPORT_GUIDE.md) - **NEW:** Troubleshooting and splitting large blueprints
- [Schematic Assembler Guide](SCHEMATIC_ASSEMBLER_README.md) - Detailed guide
- [Optimization Guide](OPTIMIZATION_GUIDE.md) - Performance improvements
- [Example Workflow Script](example_workflow.sh) - Automated conversion

## How It Works

### Block Conversion

1. Parses Minecraft block model JSON files
2. Voxelizes 3D models at texture resolution
3. Samples colors from textures
4. Exports as Scrap Mechanic blueprint

### Schematic Assembly

1. Parses Minecraft schematic (supports both old format with block IDs and new WorldEdit Version 3+ format with block states)
2. Matches blocks to generated blueprints
3. Calculates proper rotations
4. Combines into one large blueprint

## Tested With

- Tested with 5,676 block schematic
- Generated 7.8M voxel blueprint
- 99.9% block coverage (only 3 decorative blocks missing)

## License

[Add your license here]
