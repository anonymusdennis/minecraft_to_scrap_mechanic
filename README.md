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

Generates commonly-used blocks that might be missed by main.py.

```bash
python3 generate_essential_blueprints.py <assets_dir> <output_dir>
```

### 3. `schematic_to_json.py` - Schematic Converter

Converts Minecraft .schematic files (NBT format) to JSON.

```bash
python3 schematic_to_json.py <input.schematic> [output.json]
```

### 4. `schematic_assembler.py` - Schematic Assembler

Assembles a large Scrap Mechanic blueprint from a Minecraft schematic.

```bash
python3 schematic_assembler.py <schematic.json> -b <blueprints_dir> -o <output_dir> -n <name>
```

## Documentation

- [Schematic Assembler Guide](SCHEMATIC_ASSEMBLER_README.md) - Detailed guide
- [Example Workflow Script](example_workflow.sh) - Automated conversion

## How It Works

### Block Conversion

1. Parses Minecraft block model JSON files
2. Voxelizes 3D models at texture resolution
3. Samples colors from textures
4. Exports as Scrap Mechanic blueprint

### Schematic Assembly

1. Parses Minecraft schematic (block IDs and data values)
2. Matches blocks to generated blueprints
3. Calculates proper rotations
4. Combines into one large blueprint

## Tested With

- Tested with 5,676 block schematic
- Generated 7.8M voxel blueprint
- 99.9% block coverage (only 3 decorative blocks missing)

## License

[Add your license here]
