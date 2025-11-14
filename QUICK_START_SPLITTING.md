# Quick Start: Blueprint Splitting for Large Builds

Can't paste your blueprint into Scrap Mechanic? This guide shows you how to automatically split it into manageable chunks.

## Problem

You converted a Minecraft structure, but when you try to place it in Scrap Mechanic:
- ❌ Nothing happens
- ❌ Game freezes
- ❌ Game crashes
- ❌ Blueprint won't load

**Cause:** Your blueprint is too large (typically over 50,000 voxels).

## Solution: Automatic Splitting

The tool can automatically divide your blueprint into smaller chunks that work perfectly in Scrap Mechanic.

---

## Method 1: Using Convenience Scripts (Easiest)

### Windows

1. **Edit `schematic_to_blue.bat`:**
   
   Find these lines:
   ```batch
   REM     --split ^
   REM     --max-voxels-per-chunk 50000
   ```
   
   Remove `REM` to uncomment:
   ```batch
       --split ^
       --max-voxels-per-chunk 50000
   ```

2. **Run the script:**
   ```batch
   schematic_to_blue.bat my_building.schematic
   ```

### Linux/Mac

1. **Edit `schematic_to_blue.sh`:**
   
   Find these lines:
   ```bash
   # --split \
   # --max-voxels-per-chunk 50000
   ```
   
   Remove `#` to uncomment:
   ```bash
       --split \
       --max-voxels-per-chunk 50000
   ```

2. **Run the script:**
   ```bash
   ./schematic_to_blue.sh my_building.schematic
   ```

---

## Method 2: Manual Command (More Control)

### Step 1: Convert Schematic to JSON

```bash
python3 schematic_to_json.py my_building.schematic
```

### Step 2: Assemble with Splitting

```bash
python3 schematic_assembler.py my_building.json \
    --assets ./MyResourcePack/assets \
    --generate-on-demand \
    --split \
    --max-voxels-per-chunk 50000 \
    -o ./output \
    -n "MyBuilding"
```

**Adjust chunk size if needed:**
- Very large structures: `--max-voxels-per-chunk 30000`
- Medium structures: `--max-voxels-per-chunk 50000` (default)
- Small structures: Don't use `--split` at all

---

## Understanding the Output

When splitting is enabled, you'll see output like:

```
============================================================
Splitting blueprint into chunks...
  Total voxels: 125,000
  Max voxels per chunk: 50,000
  Bounding box: 160 x 80 x 120 voxels
  Chunk size: 80 x 40 x 60 voxels
  Grid: 2 x 2 x 2 = 8 chunks

  Created 8 chunks:
    Chunk 1 (0, 0, 0): 15,625 voxels
    Chunk 2 (0, 0, 1): 15,625 voxels
    ...
============================================================
```

This means your build was split into 8 separate blueprints.

---

## Installing in Scrap Mechanic

### Step 1: Find the Output Folders

After conversion, you'll have multiple UUID folders:

```
output/
├── 12345678-abcd-1234-abcd-123456789abc/
│   ├── blueprint.json
│   ├── description.json
│   └── icon.png
├── 87654321-dcba-4321-dcba-987654321cba/
│   ├── blueprint.json
│   ├── description.json
│   └── icon.png
...
```

### Step 2: Copy ALL Folders

Copy **all** the UUID folders to your Scrap Mechanic Blueprints directory:

**Windows:**
```
%AppData%\Axolot Games\Scrap Mechanic\User\User_<numbers>\Blueprints\
```

**Linux:**
```
~/.local/share/Axolot Games/Scrap Mechanic/User/User_<numbers>/Blueprints/
```

### Step 3: Launch Scrap Mechanic

Open the game and go to the Lift. You'll see multiple blueprints:
- `MyBuilding_part_1_of_8`
- `MyBuilding_part_2_of_8`
- `MyBuilding_part_3_of_8`
- etc.

### Step 4: Place the Chunks

1. **Start with part 1:** Place `MyBuilding_part_1_of_8`
2. **Enable grid mode:** Press `G` for precise alignment
3. **Place part 2 next to it:** Carefully align the edges
4. **Continue with all parts:** Place them in a grid pattern
5. **The chunks fit together** based on their original positions

**Tips:**
- Use a flat surface to place all chunks first
- Zoom in close to see alignment better
- Grid mode (G key) helps with precise placement
- Place on creative lift pad for easier assembly

---

## How Many Chunks Will I Get?

It depends on your structure's size after hollowing:

| Original Voxels | With Hollowing | Chunks (50K each) |
|-----------------|----------------|-------------------|
| 100,000 | ~5,000 | 1 (no split) |
| 500,000 | ~25,000 | 1 (no split) |
| 1,000,000 | ~50,000 | 1-2 chunks |
| 5,000,000 | ~250,000 | 5 chunks |
| 10,000,000 | ~500,000 | 10 chunks |

**Note:** Hollowing typically reduces size by 95-98%, so splitting is only needed for truly massive structures.

---

## Troubleshooting

### "I only see one blueprint, not multiple"

**Possible causes:**
- Structure was small enough to not need splitting
- Check console output - it will say "no splitting needed"

**Solution:**
- This is normal! If only one blueprint appears, the structure fits in one piece.

### "Chunks don't align properly"

**Solutions:**
1. Use grid mode (G key) in Scrap Mechanic
2. Place all chunks on a flat creative pad first
3. Zoom in close for precise alignment
4. Try placing on level ground

### "Still getting crashes with chunks"

**Solutions:**
1. Reduce chunk size: `--max-voxels-per-chunk 30000`
2. Lower graphics settings in Scrap Mechanic
3. Close other programs to free up RAM
4. Make sure hollowing is enabled (it's on by default)

### "How do I know what chunk goes where?"

**Answer:**
The chunks are indexed (0,0,0), (0,0,1), (0,1,0), etc. in 3D space:
- First number: X position (left to right)
- Second number: Y position (front to back)
- Third number: Z position (bottom to top)

Place them in a grid pattern matching these coordinates.

---

## When to Use Splitting

### ✅ Use splitting for:
- Structures with 50,000+ voxels (after hollowing)
- Builds that crash the game when placing
- Blueprints that won't load or paste
- Very large Minecraft schematics (100+ blocks in each direction)

### ❌ Don't need splitting for:
- Small to medium builds (under 50,000 voxels)
- Structures that already place successfully
- Simple houses or small builds

**Tip:** Try without splitting first. If it fails, re-run with `--split`.

---

## Advanced: Choosing Chunk Size

Default is 50,000 voxels per chunk. Adjust if needed:

**For more chunks (easier to place individually):**
```bash
--max-voxels-per-chunk 30000
```

**For fewer chunks (fewer pieces to align):**
```bash
--max-voxels-per-chunk 70000
```

**Rule of thumb:**
- 30,000: Maximum compatibility, more chunks
- 50,000: Balanced (recommended)
- 70,000: Fewer chunks, might be harder to place

---

## Quick Reference Card

```bash
# QUICK CONVERSION WITH SPLITTING

# 1. Convert schematic
python3 schematic_to_json.py building.schematic

# 2. Assemble with auto-split
python3 schematic_assembler.py building.json \
    --assets ./MyResourcePack/assets \
    --generate-on-demand \
    --split \
    -o ./output \
    -n "Building"

# 3. Copy ALL folders from ./output to:
#    %AppData%\Axolot Games\Scrap Mechanic\User\User_*/Blueprints\

# 4. Launch game and place chunks in order
```

---

## More Help

- **Full documentation:** See [BLUEPRINT_IMPORT_GUIDE.md](BLUEPRINT_IMPORT_GUIDE.md)
- **Detailed guide:** See [SCHEMATIC_ASSEMBLER_README.md](SCHEMATIC_ASSEMBLER_README.md)
- **Changelog:** See [CHANGELOG_SPLITTING_FEATURE.md](CHANGELOG_SPLITTING_FEATURE.md)

---

**Last Updated:** 2025-11-14  
**Feature Version:** Blueprint Splitting v1.0
