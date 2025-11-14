#!/usr/bin/env python3
"""
Assemble a large voxel-based Scrap Mechanic blueprint from a Minecraft schematic.

This tool:
1. Reads a Minecraft schematic JSON file
2. For each block in the schematic, determines its position and rotation
3. Loads the corresponding generated blueprint (from the converter)
4. Assembles all blocks into one large unified blueprint with correct positions and rotations
"""

import argparse
import json
import os
import sys
from uuid import uuid4
from block_ids import get_block_name
from blueprint_writer import generate_preview_image


def parse_schematic(schematic_path):
    """
    Parse a Minecraft schematic JSON file.
    Returns a dict with width, height, length, and list of blocks with positions.
    """
    with open(schematic_path, 'r') as f:
        data = json.load(f)
    
    schematic = data.get('Schematic', {})
    width = schematic['Width']
    height = schematic['Height']
    length = schematic['Length']
    blocks = schematic['Blocks']
    block_data = schematic['Data']
    
    # Parse blocks into list of (x, y, z, block_id, data_value)
    # Schematic stores blocks in YZX order
    block_list = []
    for y in range(height):
        for z in range(length):
            for x in range(width):
                index = (y * length + z) * width + x
                block_id = blocks[index]
                data_value = block_data[index]
                
                # Skip air blocks
                if block_id == 0:
                    continue
                
                block_list.append({
                    'x': x,
                    'y': y,
                    'z': z,
                    'block_id': block_id,
                    'data': data_value,
                    'name': get_block_name(block_id, data_value)
                })
    
    return {
        'width': width,
        'height': height,
        'length': length,
        'blocks': block_list
    }


def determine_rotation(block_name, data_value):
    """
    Determine Scrap Mechanic rotation based on Minecraft block data value.
    
    Returns (xaxis, zaxis) tuple for Scrap Mechanic rotation.
    Scrap Mechanic uses axis values:
    - xaxis: 1=+X (right), -1=-X (left), 2=+Y (up), -2=-Y (down), 3=+Z (forward), -3=-Z (back)
    - zaxis: defines the "up" direction of the block
    
    Default is xaxis=1 (right), zaxis=3 (forward/up in MC terms)
    """
    # Default rotation
    xaxis = 1
    zaxis = 3
    
    # Stairs, logs, and other directional blocks use data values for rotation
    # For stairs: data & 0x3 gives direction (0=east, 1=west, 2=south, 3=north)
    # Bit 2 (0x4) indicates upside-down
    
    if 'stairs' in block_name.lower():
        direction = data_value & 0x3
        upside_down = (data_value & 0x4) != 0
        
        # Map Minecraft directions to Scrap Mechanic axes
        if direction == 0:  # East (facing +X)
            xaxis = 1
            zaxis = 3
        elif direction == 1:  # West (facing -X)
            xaxis = -1
            zaxis = 3
        elif direction == 2:  # South (facing +Z)
            xaxis = 3
            zaxis = 1
        elif direction == 3:  # North (facing -Z)
            xaxis = -3
            zaxis = 1
        
        # If upside-down, flip the zaxis
        if upside_down:
            zaxis = -zaxis
    
    elif 'log' in block_name.lower() or 'wood' in block_name.lower():
        # Logs: data & 0xC gives orientation
        # 0x0 = vertical (Y-axis), 0x4 = east-west (X-axis), 0x8 = north-south (Z-axis)
        orientation = data_value & 0xC
        
        if orientation == 0x0:  # Vertical
            xaxis = 1
            zaxis = 2  # Up
        elif orientation == 0x4:  # East-West (X-axis)
            xaxis = 2
            zaxis = 1
        elif orientation == 0x8:  # North-South (Z-axis)
            xaxis = 1
            zaxis = 3
    
    elif 'slab' in block_name.lower():
        # Slabs: bit 3 (0x8) indicates top half
        top_half = (data_value & 0x8) != 0
        if top_half:
            zaxis = 2  # Up
        else:
            zaxis = -2  # Down
    
    elif 'torch' in block_name.lower():
        # Torches: 1=east, 2=west, 3=south, 4=north, 5=standing
        direction = data_value
        
        if direction == 5:  # Standing (on ground)
            xaxis = 1
            zaxis = 2
        elif direction == 1:  # East wall
            xaxis = 1
            zaxis = 3
        elif direction == 2:  # West wall
            xaxis = -1
            zaxis = 3
        elif direction == 3:  # South wall
            xaxis = 3
            zaxis = 1
        elif direction == 4:  # North wall
            xaxis = -3
            zaxis = 1
    
    elif 'button' in block_name.lower() or 'lever' in block_name.lower():
        # Similar to torches but different values
        direction = data_value & 0x7
        
        if direction == 0:  # Down
            xaxis = 1
            zaxis = -2
        elif direction == 5:  # Up
            xaxis = 1
            zaxis = 2
        elif direction == 1:  # East wall
            xaxis = 1
            zaxis = 3
        elif direction == 2:  # West wall
            xaxis = -1
            zaxis = 3
        elif direction == 3:  # South wall
            xaxis = 3
            zaxis = 1
        elif direction == 4:  # North wall
            xaxis = -3
            zaxis = 1
    
    elif 'fence_gate' in block_name.lower() or 'door' in block_name.lower():
        # Gates/doors: data & 0x3 gives direction
        direction = data_value & 0x3
        
        if direction == 0:  # South
            xaxis = 3
            zaxis = 1
        elif direction == 1:  # West
            xaxis = -1
            zaxis = 3
        elif direction == 2:  # North
            xaxis = -3
            zaxis = 1
        elif direction == 3:  # East
            xaxis = 1
            zaxis = 3
    
    return (xaxis, zaxis)


def load_blueprint_blocks(blueprint_folder, block_name):
    """
    Load blocks from a generated blueprint folder.
    Returns list of block dicts with relative positions and properties.
    """
    # Try to find the blueprint by name
    # Blueprints are stored in UUID folders with description.json containing the name
    
    if not os.path.isdir(blueprint_folder):
        print(f"Warning: Blueprint folder not found: {blueprint_folder}")
        return []
    
    # Normalize the block name for matching
    normalized_name = block_name.lower().replace('_', '')
    
    # Try various name variations
    # For example: "stone_slab" -> ["stone_slab", "stoneslab", "stone", "slab"]
    name_variations = [
        block_name.lower(),
        normalized_name,
    ]
    
    # Add component-based variations
    parts = block_name.lower().split('_')
    if len(parts) > 1:
        # Try with just the material (e.g., "oak" from "oak_planks")
        name_variations.append(parts[0])
        # Try with just the type (e.g., "planks" from "oak_planks")
        name_variations.append(parts[-1])
        # Try material + type without underscores
        name_variations.append(''.join(parts))
    
    # Search for blueprint with matching name
    for folder_name in os.listdir(blueprint_folder):
        folder_path = os.path.join(blueprint_folder, folder_name)
        if not os.path.isdir(folder_path):
            continue
        
        desc_path = os.path.join(folder_path, "description.json")
        if not os.path.isfile(desc_path):
            continue
        
        try:
            with open(desc_path, 'r') as f:
                desc = json.load(f)
            
            # Check if name matches (normalize for comparison)
            bp_name = desc.get('name', '').lower()
            bp_name_normalized = bp_name.replace('_', '')
            
            # Check all name variations
            match_found = False
            for variant in name_variations:
                if variant in bp_name or variant in bp_name_normalized:
                    match_found = True
                    break
                # Also check if blueprint name contains the variant
                if bp_name in variant or bp_name_normalized in variant:
                    match_found = True
                    break
            
            if match_found:
                # Found matching blueprint, load it
                blueprint_path = os.path.join(folder_path, "blueprint.json")
                if not os.path.isfile(blueprint_path):
                    continue
                
                with open(blueprint_path, 'r') as f:
                    blueprint = json.load(f)
                
                # Extract blocks from the blueprint
                blocks = []
                for body in blueprint.get('bodies', []):
                    for child in body.get('childs', []):
                        blocks.append({
                            'pos': child['pos'],
                            'color': child.get('color'),
                            'shapeId': child.get('shapeId'),
                            'bounds': child.get('bounds', {'x': 1, 'y': 1, 'z': 1})
                        })
                
                return blocks
        except Exception as e:
            print(f"Error loading blueprint {folder_path}: {e}")
            continue
    
    # Blueprint not found
    return []


def rotate_position(pos, xaxis, zaxis):
    """
    Rotate a position vector according to xaxis and zaxis.
    This is a simplified rotation - in practice, you'd need proper 3D rotation matrices.
    For now, we'll just adjust the position based on the axes.
    """
    x, y, z = pos['x'], pos['y'], pos['z']
    
    # This is a simplified approach - proper rotation would require matrix math
    # For basic rotations around Y axis (most common in MC):
    if xaxis == 1 and zaxis == 3:  # No rotation
        return {'x': x, 'y': y, 'z': z}
    elif xaxis == -1 and zaxis == 3:  # 180 degrees
        return {'x': -x, 'y': y, 'z': -z}
    elif xaxis == 3 and zaxis == 1:  # 90 degrees CW
        return {'x': z, 'y': y, 'z': -x}
    elif xaxis == -3 and zaxis == 1:  # 90 degrees CCW
        return {'x': -z, 'y': y, 'z': x}
    else:
        # For more complex rotations, just return as-is for now
        return {'x': x, 'y': y, 'z': z}


def hollow_out_blueprint(blueprint):
    """
    Remove interior parts from a blueprint, keeping only the outer shell.
    This significantly reduces part count for large structures.
    
    :param blueprint: Blueprint dict with 'bodies' containing 'childs' list
    :return: Modified blueprint with interior parts removed
    """
    if not blueprint.get('bodies') or not blueprint['bodies'][0].get('childs'):
        return blueprint
    
    parts = blueprint['bodies'][0]['childs']
    
    if len(parts) == 0:
        return blueprint
    
    # Build a set of all occupied positions
    position_map = {}
    for i, part in enumerate(parts):
        pos = part['pos']
        key = (pos['x'], pos['y'], pos['z'])
        position_map[key] = i
    
    # Determine which parts are on the surface
    surface_parts = []
    
    for part in parts:
        pos = part['pos']
        x, y, z = pos['x'], pos['y'], pos['z']
        
        # Check all 6 neighbors
        neighbors = [
            (x+1, y, z), (x-1, y, z),
            (x, y+1, z), (x, y-1, z),
            (x, y, z+1), (x, y, z-1)
        ]
        
        # If any neighbor is missing, this is a surface part
        is_surface = False
        for neighbor in neighbors:
            if neighbor not in position_map:
                is_surface = True
                break
        
        if is_surface:
            surface_parts.append(part)
    
    # Update blueprint with only surface parts
    blueprint['bodies'][0]['childs'] = surface_parts
    
    return blueprint

def assemble_blueprint(schematic_data, blueprints_folder, output_dir, blueprint_name, hollow=False):
    """
    Assemble a large blueprint from schematic data using individual block blueprints.
    
    :param hollow: if True, hollow out interior parts to reduce part count
    """
    print(f"Assembling blueprint from {len(schematic_data['blocks'])} blocks...")
    
    # Create output folder
    bp_id = str(uuid4())
    bp_folder = os.path.join(output_dir, bp_id)
    os.makedirs(bp_folder, exist_ok=True)
    
    # Initialize blueprint structure
    blueprint = {
        "bodies": [{"childs": []}],
        "version": 4
    }
    
    # Track statistics
    stats = {
        'total_blocks': 0,
        'blocks_added': 0,
        'blocks_skipped': 0,
        'missing_blueprints': set()
    }
    
    # Cache for loaded blueprints to avoid repeated disk access
    blueprint_cache = {}
    
    # Process each block in the schematic
    for idx, mc_block in enumerate(schematic_data['blocks']):
        stats['total_blocks'] += 1
        
        # Progress logging every 100 blocks
        if idx % 100 == 0:
            print(f"Processing block {idx + 1}/{len(schematic_data['blocks'])}...")
        
        # Get block position in schematic
        base_x = mc_block['x']
        base_y = mc_block['y']
        base_z = mc_block['z']
        block_name = mc_block['name']
        data_value = mc_block['data']
        
        # Determine rotation
        xaxis, zaxis = determine_rotation(block_name, data_value)
        
        # Load blueprint for this block type (with caching)
        if block_name in blueprint_cache:
            block_blueprints = blueprint_cache[block_name]
        else:
            block_blueprints = load_blueprint_blocks(blueprints_folder, block_name)
            blueprint_cache[block_name] = block_blueprints
        
        if not block_blueprints:
            stats['blocks_skipped'] += 1
            stats['missing_blueprints'].add(block_name)
            # Create a default cube block as fallback
            block_blueprints = [{
                'pos': {'x': 0, 'y': 0, 'z': 0},
                'color': '808080',  # Gray
                'shapeId': '628b2d61-5ceb-43e9-8334-a4135566df7a',  # Plastic
                'bounds': {'x': 1, 'y': 1, 'z': 1}
            }]
        
        # Add each voxel from the block blueprint
        for voxel in block_blueprints:
            # Get relative position within the block
            rel_pos = voxel['pos']
            
            # Rotate relative position according to block rotation
            rotated_pos = rotate_position(rel_pos, xaxis, zaxis)
            
            # Calculate absolute position in the large blueprint
            # Note: Scrap Mechanic uses different axis mapping than Minecraft
            # MC: X=east, Y=up, Z=south
            # SM: X=right, Y=forward, Z=up
            abs_pos = {
                'x': base_x + rotated_pos['x'],
                'y': base_z + rotated_pos['z'],  # MC Z -> SM Y
                'z': base_y + rotated_pos['y']   # MC Y -> SM Z
            }
            
            # Create block entry for blueprint
            part = {
                "bounds": voxel.get('bounds', {"x": 1, "y": 1, "z": 1}),
                "shapeId": voxel.get('shapeId', '628b2d61-5ceb-43e9-8334-a4135566df7a'),
                "color": voxel.get('color', '808080'),
                "pos": abs_pos,
                "xaxis": xaxis,
                "zaxis": zaxis
            }
            
            blueprint["bodies"][0]["childs"].append(part)
            stats['blocks_added'] += 1
    
    # Hollow out if requested
    if hollow:
        original_count = len(blueprint["bodies"][0]["childs"])
        print(f"\nHollowing out blueprint...")
        blueprint = hollow_out_blueprint(blueprint)
        new_count = len(blueprint["bodies"][0]["childs"])
        print(f"  Parts reduced: {original_count} -> {new_count} ({100*(1-new_count/original_count):.1f}% reduction)")
    
    # Write blueprint.json
    blueprint_path = os.path.join(bp_folder, "blueprint.json")
    with open(blueprint_path, 'w') as f:
        json.dump(blueprint, f, separators=(',', ':'))
    
    # Write description.json
    desc = {
        "description": f"Voxel copy of Minecraft schematic - {schematic_data['width']}x{schematic_data['height']}x{schematic_data['length']}",
        "localId": bp_id,
        "name": blueprint_name,
        "type": "Blueprint",
        "version": 0
    }
    desc_path = os.path.join(bp_folder, "description.json")
    with open(desc_path, 'w') as f:
        json.dump(desc, f, indent=2)
    
    # Generate preview image from blueprint parts
    print(f"\nGenerating preview image...")
    voxel_colors = {}
    for part in blueprint["bodies"][0]["childs"]:
        pos = part['pos']
        # Convert hex color back to RGB
        color_hex = part['color']
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        voxel_colors[(pos['x'], pos['y'], pos['z'])] = (r, g, b, 255)
    
    generate_preview_image(voxel_colors, bp_folder)
    
    # Print statistics
    print(f"\nAssembly complete!")
    print(f"  Total MC blocks: {stats['total_blocks']}")
    print(f"  Voxels added: {stats['blocks_added']}")
    print(f"  Blocks skipped: {stats['blocks_skipped']}")
    if stats['missing_blueprints']:
        print(f"  Missing blueprints ({len(stats['missing_blueprints'])}):")
        for name in sorted(stats['missing_blueprints'])[:10]:
            print(f"    - {name}")
        if len(stats['missing_blueprints']) > 10:
            print(f"    ... and {len(stats['missing_blueprints']) - 10} more")
    print(f"\nBlueprint saved to: {bp_folder}")
    
    return bp_folder


def main():
    parser = argparse.ArgumentParser(
        description="Assemble a large Scrap Mechanic blueprint from a Minecraft schematic"
    )
    parser.add_argument(
        "schematic",
        help="Path to the Minecraft schematic JSON file"
    )
    parser.add_argument(
        "--blueprints", "-b",
        required=True,
        help="Path to the folder containing generated block blueprints"
    )
    parser.add_argument(
        "--output", "-o",
        default="./assembled_blueprints",
        help="Output directory for the assembled blueprint (default: ./assembled_blueprints)"
    )
    parser.add_argument(
        "--name", "-n",
        default="MinecraftSchematic",
        help="Name for the assembled blueprint (default: MinecraftSchematic)"
    )
    parser.add_argument(
        "--hollow",
        action="store_true",
        help="Hollow out the blueprint to remove interior parts and reduce part count. Recommended for large structures to prevent crashes."
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.isfile(args.schematic):
        print(f"Error: Schematic file not found: {args.schematic}")
        return 1
    
    if not os.path.isdir(args.blueprints):
        print(f"Error: Blueprints folder not found: {args.blueprints}")
        return 1
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Parse schematic
    print(f"Parsing schematic: {args.schematic}")
    schematic_data = parse_schematic(args.schematic)
    print(f"  Dimensions: {schematic_data['width']}x{schematic_data['height']}x{schematic_data['length']}")
    print(f"  Non-air blocks: {len(schematic_data['blocks'])}")
    
    # Assemble blueprint
    assemble_blueprint(schematic_data, args.blueprints, args.output, args.name, hollow=args.hollow)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
