#!/usr/bin/env python3
"""
Generate essential block blueprints that are commonly used in schematics.
This supplements the main.py converter which only processes files directly in the models/block/ directory.
"""

import os
import sys
from model_parser import load_model, resolve_model
from voxelizer import voxelize_model
from blueprint_writer import export_blueprint

def generate_essential_blocks(assets_dir, output_dir):
    """Generate blueprints for commonly used blocks that may be missed by main.py"""
    
    # Essential blocks that are often referenced by schematic data
    essential_blocks = [
        # Basic blocks
        ('anvil', 'anvil'),
        ('glowstone', 'glowstone'),
        ('grass_block', 'grass_block'),
        ('ladder', 'ladder'),
        ('glass', 'glass'),
        
        # Torches
        ('torch', 'torch'),
        ('redstone_torch', 'redstone_torch'),
        
        # Redstone components
        ('tripwire_hook', 'tripwire_hook'),
        
        # Snow layers (default to 2-layer snow)
        ('snow_height2', 'snow'),
        
        # Bells (default to floor bell)
        ('bell_floor', 'bell'),
        
        # Scaffolding (default to stable)
        ('scaffolding_stable', 'scaffolding'),
        
        # Iron bars (default to post)
        ('iron_bars_post', 'iron_bars'),
        
        # Trapdoors (bottom version for basic form)
        ('oak_trapdoor_bottom', 'oak_trapdoor'),
        ('spruce_trapdoor_bottom', 'spruce_trapdoor'),
        ('birch_trapdoor_bottom', 'birch_trapdoor'),
        ('jungle_trapdoor_bottom', 'jungle_trapdoor'),
        ('acacia_trapdoor_bottom', 'acacia_trapdoor'),
        ('dark_oak_trapdoor_bottom', 'dark_oak_trapdoor'),
        ('iron_trapdoor_bottom', 'iron_trapdoor'),
        
        # Doors (bottom version for basic form)
        ('oak_door_bottom', 'oak_door'),
        ('spruce_door_bottom', 'spruce_door'),
        ('birch_door_bottom', 'birch_door'),
        ('jungle_door_bottom', 'jungle_door'),
        ('acacia_door_bottom', 'acacia_door'),
        ('dark_oak_door_bottom', 'dark_oak_door'),
        
        # Wooden slabs
        ('oak_slab', 'oak_slab'),
        ('spruce_slab', 'spruce_slab'),
        ('birch_slab', 'birch_slab'),
        ('jungle_slab', 'jungle_slab'),
        ('acacia_slab', 'acacia_slab'),
        ('dark_oak_slab', 'dark_oak_slab'),
    ]
    
    # Stained glass panes (all colors)
    colors = ['white', 'orange', 'magenta', 'light_blue', 'yellow', 'lime', 'pink', 'gray',
              'light_gray', 'cyan', 'purple', 'blue', 'brown', 'green', 'red', 'black']
    
    for color in colors:
        model_name = f"{color}_stained_glass_pane_post"
        export_name = f"{color}_stained_glass_pane"
        essential_blocks.append((model_name, export_name))
    
    print(f"Generating {len(essential_blocks)} essential block blueprints...")
    print(f"Assets directory: {assets_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for model_name, export_name in essential_blocks:
        model_path = f"minecraft:block/{model_name}"
        try:
            model = load_model(model_path, assets_dir)
            
            if "elements" not in model or len(model.get("elements", [])) == 0:
                skip_count += 1
                continue
            
            resolved_elems = resolve_model(model, assets_dir)
            voxel_colors = voxelize_model(resolved_elems, {})
            
            if len(voxel_colors) == 0:
                skip_count += 1
                continue
            
            export_blueprint(voxel_colors, output_dir, export_name, model_name)
            success_count += 1
            print(f"✓ {export_name} ({len(voxel_colors)} voxels)")
            
        except Exception as e:
            error_count += 1
            print(f"✗ {export_name}: {e}")
    
    # Generate simple fallback cubes for entity blocks that don't have geometry models
    # or blocks with very thin geometry that don't voxelize well
    print("\nGenerating fallback cubes for entity blocks and thin blocks...")
    entity_blocks = [
        ('chest', (139, 69, 19)),      # Brown/chest color
        ('red_bed', (160, 39, 34)),    # Red color
        ('waxed_copper_chest', (139, 69, 19)),  # Same as chest
        ('glass', (208, 234, 233)),    # Light blue/glass color (from texture)
        ('iron_bars', (128, 128, 128)), # Gray/iron color
        ('spruce_door', (108, 84, 60)), # Spruce/brown door color
    ]
    
    for block_name, color_rgb in entity_blocks:
        try:
            # Create a simple 16x16x16 voxel cube
            voxel_colors = {}
            for x in range(16):
                for y in range(16):
                    for z in range(16):
                        voxel_colors[(x, y, z)] = (*color_rgb, 255)
            
            export_blueprint(voxel_colors, output_dir, block_name, block_name)
            success_count += 1
            print(f"✓ {block_name} (fallback cube, {len(voxel_colors)} voxels)")
        except Exception as e:
            error_count += 1
            print(f"✗ {block_name}: {e}")
    
    print()
    print(f"Summary:")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(essential_blocks) + len(entity_blocks)}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_essential_blueprints.py <assets_dir> <output_dir>")
        print()
        print("Example:")
        print("  python3 generate_essential_blueprints.py ./MyResourcePack/assets ./blueprints")
        print()
        print("This script generates blueprints for commonly used blocks that may not be")
        print("included when running main.py. Run this AFTER main.py to supplement the")
        print("generated blueprints.")
        return 1
    
    assets_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.isdir(assets_dir):
        print(f"Error: Assets directory not found: {assets_dir}")
        return 1
    
    generate_essential_blocks(assets_dir, output_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
