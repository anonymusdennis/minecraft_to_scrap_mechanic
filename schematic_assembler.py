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
from blueprint_writer import generate_preview_image, rgba_to_hex, get_shape_id_for_block


def parse_block_state(block_state):
    """
    Parse a block state string like "minecraft:stone" or "minecraft:oak_stairs[facing=east,half=bottom]"
    Returns (block_name, properties_dict)
    """
    # Remove minecraft: prefix if present
    if ':' in block_state:
        block_state = block_state.split(':', 1)[1]
    
    # Split block name from properties
    if '[' in block_state:
        block_name = block_state.split('[')[0]
        # Extract properties (if needed in the future)
        props_str = block_state.split('[')[1].rstrip(']')
        properties = {}
        if props_str:
            for prop in props_str.split(','):
                if '=' in prop:
                    key, value = prop.split('=', 1)
                    properties[key] = value
        return block_name, properties
    else:
        return block_state, {}


def parse_schematic(schematic_path):
    """
    Parse a Minecraft schematic JSON file (supports both old and new WorldEdit formats).
    Returns a dict with width, height, length, and list of blocks with positions.
    """
    with open(schematic_path, 'r') as f:
        data = json.load(f)
    
    # Handle both root-level Schematic and nested structure (e.g., "": {"Schematic": {...}})
    if 'Schematic' in data:
        schematic = data['Schematic']
    elif '' in data and 'Schematic' in data['']:
        schematic = data['']['Schematic']
    else:
        raise ValueError("Invalid schematic format: 'Schematic' key not found")
    
    width = schematic['Width']
    height = schematic['Height']
    length = schematic['Length']
    
    # Detect format version
    blocks_data = schematic['Blocks']
    
    # Check if this is the new WorldEdit format (Version 3+)
    # New format has Blocks as a dict with 'Palette' and 'Data'
    # Old format has Blocks as a list/array
    is_new_format = isinstance(blocks_data, dict) and 'Palette' in blocks_data and 'Data' in blocks_data
    
    block_list = []
    
    if is_new_format:
        # New WorldEdit format (Version 3+)
        palette = blocks_data['Palette']
        data_array = blocks_data['Data']
        
        # Create reverse mapping: palette_id -> block_state_string
        id_to_block_state = {v: k for k, v in palette.items()}
        
        # Parse blocks into list of (x, y, z, block_name, properties)
        # Schematic stores blocks in YZX order
        for y in range(height):
            for z in range(length):
                for x in range(width):
                    index = (y * length + z) * width + x
                    palette_id = data_array[index]
                    
                    # Get block state from palette
                    block_state = id_to_block_state.get(palette_id, 'minecraft:air')
                    block_name, properties = parse_block_state(block_state)
                    
                    # Skip air blocks
                    if block_name == 'air':
                        continue
                    
                    block_list.append({
                        'x': x,
                        'y': y,
                        'z': z,
                        'block_id': None,  # No numeric ID in new format
                        'data': 0,  # No separate data value in new format
                        'name': block_name,
                        'properties': properties,
                        'block_state': block_state
                    })
    else:
        # Old format (pre-1.13, uses numeric block IDs)
        blocks = blocks_data
        block_data = schematic['Data']
        
        # Parse blocks into list of (x, y, z, block_id, data_value)
        # Schematic stores blocks in YZX order
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


def generate_block_on_demand(block_name, assets_dir):
    """
    Generate a block blueprint on-demand if it doesn't exist in the cache.
    Returns list of block voxels with positions and properties.
    """
    try:
        from model_parser import load_model, resolve_model
        from voxelizer import voxelize_model
        
        model_path = f"minecraft:block/{block_name}"
        model = load_model(model_path, assets_dir)
        
        if 'elements' not in model or len(model['elements']) == 0:
            return None
            
        resolved_elems = resolve_model(model, assets_dir)
        voxel_colors = voxelize_model(resolved_elems, {})
        
        if len(voxel_colors) == 0:
            return None
        
        # Convert voxel colors to block format
        blocks = []
        shape_id = get_shape_id_for_block(block_name)
        
        for (x, y, z), color in voxel_colors.items():
            # Skip fully transparent voxels
            if len(color) > 3 and color[3] == 0:
                continue
            
            blocks.append({
                'pos': {'x': x, 'y': z, 'z': y},  # Note: pos.y = z index, pos.z = y index
                'color': rgba_to_hex(color),
                'shapeId': shape_id,
                'bounds': {'x': 1, 'y': 1, 'z': 1}
            })
        
        return blocks
    except Exception as e:
        # Block model not found or error generating
        return None


def load_blueprint_blocks(blueprint_folder, block_name, assets_dir=None, generate_on_demand=False):
    """
    Load blocks from a generated blueprint folder, or generate on-demand if enabled.
    Returns list of block dicts with relative positions and properties.
    """
    # Try to find the blueprint by name
    # Blueprints are stored in UUID folders with description.json containing the name
    
    if not os.path.isdir(blueprint_folder):
        if generate_on_demand and assets_dir:
            # Generate block on-demand
            return generate_block_on_demand(block_name, assets_dir) or []
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
    
    # Blueprint not found in cache
    if generate_on_demand and assets_dir:
        # Generate block on-demand
        return generate_block_on_demand(block_name, assets_dir) or []
    
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
    Intelligently remove interior voxels from a blueprint to reduce part count
    while maintaining structural integrity.
    
    Strategy:
    1. Keep all surface voxels (those with at least one empty neighbor)
    2. Use BFS to calculate distance from surface for each voxel
    3. Remove voxels that are far from surface (interior)
    4. Use 1-thick walls where possible, but keep thicker walls to prevent
       floating parts or structural issues
    
    :param blueprint: Blueprint dict with 'bodies' containing 'childs' list
    :return: Modified blueprint with interior voxels removed
    """
    if not blueprint.get('bodies') or not blueprint['bodies'][0].get('childs'):
        return blueprint
    
    parts = blueprint['bodies'][0]['childs']
    
    if len(parts) == 0:
        return blueprint
    
    # Build a map of all occupied positions
    position_map = {}
    for i, part in enumerate(parts):
        pos = part['pos']
        key = (pos['x'], pos['y'], pos['z'])
        position_map[key] = i
    
    # Calculate distance from surface for each voxel using BFS
    from collections import deque
    
    distance = {}
    queue = deque()
    
    # Find all surface voxels (distance 0)
    for part in parts:
        pos = part['pos']
        x, y, z = pos['x'], pos['y'], pos['z']
        
        # Check all 6 neighbors
        neighbors = [
            (x+1, y, z), (x-1, y, z),
            (x, y+1, z), (x, y-1, z),
            (x, y, z+1), (x, y, z-1)
        ]
        
        # If any neighbor is missing, this is a surface voxel
        is_surface = False
        for neighbor in neighbors:
            if neighbor not in position_map:
                is_surface = True
                break
        
        if is_surface:
            key = (x, y, z)
            distance[key] = 0
            queue.append(key)
    
    # BFS to calculate distance from surface
    while queue:
        current = queue.popleft()
        x, y, z = current
        current_dist = distance[current]
        
        # Check all 6 neighbors
        neighbors = [
            (x+1, y, z), (x-1, y, z),
            (x, y+1, z), (x, y-1, z),
            (x, y, z+1), (x, y, z-1)
        ]
        
        for neighbor in neighbors:
            if neighbor in position_map and neighbor not in distance:
                distance[neighbor] = current_dist + 1
                queue.append(neighbor)
    
    # Keep voxels based on distance from surface
    # Use adaptive thickness: keep voxels within distance 1 of surface
    # (This creates a 1-2 voxel thick shell depending on geometry)
    kept_parts = []
    
    for part in parts:
        pos = part['pos']
        key = (pos['x'], pos['y'], pos['z'])
        
        # Keep if on surface or very close to it
        if distance.get(key, 0) <= 1:
            kept_parts.append(part)
    
    # NOTE: Removed connectivity verification that was causing the bug where only
    # one block's voxels were kept. The connectivity check assumed all voxels should
    # be touching, but when assembling from individual block blueprints spaced
    # VOXEL_SCALE (16) units apart, blocks are intentionally not touching.
    # The distance-based filtering above is sufficient to hollow out each block
    # individually while preserving all blocks in the structure.
    
    # Update blueprint with kept parts
    blueprint['bodies'][0]['childs'] = kept_parts
    
    return blueprint

def deduplicate_voxels(blueprint):
    """
    Remove overlapping voxels that occupy the same position.
    When multiple voxels exist at the same position, keeps only the last one added.
    This prevents game crashes caused by overlapping parts.
    
    :param blueprint: Blueprint dict with 'bodies' containing 'childs' list
    :return: Modified blueprint with overlapping voxels removed
    """
    if not blueprint.get('bodies') or not blueprint['bodies'][0].get('childs'):
        return blueprint
    
    parts = blueprint['bodies'][0]['childs']
    
    if len(parts) == 0:
        return blueprint
    
    # Deduplicate by rebuilding with unique positions only
    # Process in reverse to keep the last occurrence at each position
    final_parts = []
    seen_positions = set()
    
    for part in reversed(parts):
        pos = part['pos']
        key = (pos['x'], pos['y'], pos['z'])
        
        if key not in seen_positions:
            seen_positions.add(key)
            final_parts.append(part)
    
    # Reverse back to maintain original order
    final_parts.reverse()
    
    # Update blueprint with deduplicated parts
    blueprint['bodies'][0]['childs'] = final_parts
    
    return blueprint


def split_blueprint_into_chunks(blueprint, max_voxels_per_chunk=50000, chunk_size=None):
    """
    Split a large blueprint into multiple smaller blueprints for easier handling in Scrap Mechanic.
    
    This is useful for very large structures that may be difficult to place or load as a single blueprint.
    The structure is divided into spatial chunks, and each chunk is saved as a separate blueprint.
    
    :param blueprint: Blueprint dict with 'bodies' containing 'childs' list
    :param max_voxels_per_chunk: Maximum number of voxels per chunk (default: 50000)
    :param chunk_size: Override automatic chunking with fixed chunk size (x, y, z) in voxels
    :return: List of blueprint dicts, one for each chunk
    """
    if not blueprint.get('bodies') or not blueprint['bodies'][0].get('childs'):
        return [blueprint]
    
    parts = blueprint['bodies'][0]['childs']
    
    if len(parts) == 0:
        return [blueprint]
    
    # If blueprint is small enough, don't split
    if len(parts) <= max_voxels_per_chunk:
        print(f"  Blueprint has {len(parts)} voxels, no splitting needed (threshold: {max_voxels_per_chunk})")
        return [blueprint]
    
    print(f"\n{'='*60}")
    print(f"Splitting blueprint into chunks...")
    print(f"  Total voxels: {len(parts)}")
    print(f"  Max voxels per chunk: {max_voxels_per_chunk}")
    
    # Find bounding box
    min_x = min(p['pos']['x'] for p in parts)
    max_x = max(p['pos']['x'] for p in parts)
    min_y = min(p['pos']['y'] for p in parts)
    max_y = max(p['pos']['y'] for p in parts)
    min_z = min(p['pos']['z'] for p in parts)
    max_z = max(p['pos']['z'] for p in parts)
    
    total_x = max_x - min_x + 1
    total_y = max_y - min_y + 1
    total_z = max_z - min_z + 1
    
    print(f"  Bounding box: {total_x} x {total_y} x {total_z} voxels")
    
    # Determine chunk size if not specified
    if chunk_size is None:
        # Calculate how many chunks we need
        num_chunks_needed = (len(parts) + max_voxels_per_chunk - 1) // max_voxels_per_chunk
        
        # Try to split along the longest axis first, then distribute across other axes
        # This creates more rectangular chunks rather than thin slices
        axes = [
            ('x', total_x, min_x, max_x),
            ('y', total_y, min_y, max_y),
            ('z', total_z, min_z, max_z)
        ]
        axes.sort(key=lambda a: a[1], reverse=True)  # Sort by size, largest first
        
        # Estimate chunks per axis
        # Start with splitting the longest axis
        import math
        splits_per_axis = [1, 1, 1]
        axis_names = [a[0] for a in axes]
        
        # Simple heuristic: try to split evenly across all axes
        # aiming for roughly cubic chunks
        volume = total_x * total_y * total_z
        voxels_per_chunk_target = volume / num_chunks_needed if num_chunks_needed > 0 else volume
        chunk_dimension = max(1, int(voxels_per_chunk_target ** (1/3)))
        
        chunk_x = max(1, int(total_x / max(1, total_x // chunk_dimension)))
        chunk_y = max(1, int(total_y / max(1, total_y // chunk_dimension)))
        chunk_z = max(1, int(total_z / max(1, total_z // chunk_dimension)))
        
        chunk_size = (chunk_x, chunk_y, chunk_z)
    
    chunk_x, chunk_y, chunk_z = chunk_size
    print(f"  Chunk size: {chunk_x} x {chunk_y} x {chunk_z} voxels")
    
    # Calculate number of chunks in each dimension
    num_chunks_x = (total_x + chunk_x - 1) // chunk_x
    num_chunks_y = (total_y + chunk_y - 1) // chunk_y
    num_chunks_z = (total_z + chunk_z - 1) // chunk_z
    
    print(f"  Grid: {num_chunks_x} x {num_chunks_y} x {num_chunks_z} = {num_chunks_x * num_chunks_y * num_chunks_z} chunks")
    
    # Create chunks
    chunks = {}
    
    for part in parts:
        pos = part['pos']
        x, y, z = pos['x'], pos['y'], pos['z']
        
        # Determine which chunk this voxel belongs to
        chunk_idx_x = (x - min_x) // chunk_x
        chunk_idx_y = (y - min_y) // chunk_y
        chunk_idx_z = (z - min_z) // chunk_z
        
        chunk_key = (chunk_idx_x, chunk_idx_y, chunk_idx_z)
        
        if chunk_key not in chunks:
            chunks[chunk_key] = []
        
        chunks[chunk_key].append(part)
    
    # Convert chunks dict to list of blueprints
    blueprint_chunks = []
    
    for chunk_key, chunk_parts in sorted(chunks.items()):
        chunk_blueprint = {
            "bodies": [{"childs": chunk_parts}],
            "version": 4
        }
        blueprint_chunks.append({
            'blueprint': chunk_blueprint,
            'chunk_index': chunk_key,
            'voxel_count': len(chunk_parts)
        })
    
    # Print chunk statistics
    print(f"\n  Created {len(blueprint_chunks)} chunks:")
    for i, chunk_info in enumerate(blueprint_chunks):
        idx = chunk_info['chunk_index']
        count = chunk_info['voxel_count']
        print(f"    Chunk {i+1} ({idx[0]}, {idx[1]}, {idx[2]}): {count} voxels")
    
    print(f"{'='*60}\n")
    
    return blueprint_chunks


def assemble_blueprint(schematic_data, blueprints_folder, output_dir, blueprint_name, hollow=False, assets_dir=None, generate_on_demand=False, split_chunks=False, max_voxels_per_chunk=50000):
    """
    Assemble a large blueprint from schematic data using individual block blueprints.
    
    :param hollow: if True, hollow out interior parts to reduce part count
    :param assets_dir: Path to Minecraft assets for on-demand block generation
    :param generate_on_demand: If True, generate missing blocks on-demand instead of using pre-generated blueprints
    :param split_chunks: if True, split large blueprints into multiple smaller chunks
    :param max_voxels_per_chunk: maximum voxels per chunk when splitting (default: 50000)
    """
    # Minecraft blocks are 1m cubes, but Scrap Mechanic blocks are made of 16x16x16 voxels (each voxel is 0.25m)
    # Therefore, we need to scale Minecraft coordinates by 16 to get proper Scrap Mechanic voxel positions
    VOXEL_SCALE = 16
    
    print(f"Assembling blueprint from {len(schematic_data['blocks'])} blocks...")
    print(f"Schematic dimensions: {schematic_data['width']}x{schematic_data['height']}x{schematic_data['length']} blocks")
    print(f"Using voxel scale factor: {VOXEL_SCALE} (Minecraft 1m block = {VOXEL_SCALE} Scrap Mechanic voxels)")
    
    if generate_on_demand:
        if not assets_dir:
            print("Warning: On-demand generation requested but no assets_dir provided. Falling back to pre-generated blueprints.")
            generate_on_demand = False
        else:
            print(f"On-demand block generation enabled. Blocks will be generated as needed from {assets_dir}")
    
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
        'missing_blueprints': set(),
        'voxels_before_dedup': 0,
        'voxels_after_dedup': 0,
        'overlapping_voxels_removed': 0
    }
    
    # Cache for loaded blueprints to avoid repeated disk access
    blueprint_cache = {}
    
    # Process each block in the schematic
    for idx, mc_block in enumerate(schematic_data['blocks']):
        stats['total_blocks'] += 1
        
        # Progress logging every 100 blocks
        if idx % 100 == 0:
            print(f"Processing block {idx + 1}/{len(schematic_data['blocks'])} ({100*idx//len(schematic_data['blocks'])}%)...")
        
        # Get block position in schematic
        base_x = mc_block['x']
        base_y = mc_block['y']
        base_z = mc_block['z']
        block_name = mc_block['name']
        data_value = mc_block['data']
        
        # Log first few blocks for debugging
        if idx < 3:
            print(f"  Block {idx}: '{block_name}' at MC pos ({base_x}, {base_y}, {base_z}), data={data_value}")
        
        # Determine rotation for the entire block
        xaxis, zaxis = determine_rotation(block_name, data_value)
        
        # Load blueprint for this block type (with caching)
        if block_name in blueprint_cache:
            block_blueprints = blueprint_cache[block_name]
        else:
            block_blueprints = load_blueprint_blocks(blueprints_folder, block_name, assets_dir, generate_on_demand)
            blueprint_cache[block_name] = block_blueprints
            if idx < 3 and block_blueprints:
                print(f"    Loaded blueprint with {len(block_blueprints)} voxels")
        
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
            if idx < 3:
                print(f"    Using default gray cube fallback")
        
        # Add each voxel from the block blueprint
        for voxel in block_blueprints:
            # Get relative position within the block
            rel_pos = voxel['pos']
            
            # Rotate relative position according to block rotation
            rotated_pos = rotate_position(rel_pos, xaxis, zaxis)
            
            # Calculate absolute position in the large blueprint with proper scaling
            # Key fix: Multiply Minecraft block coordinates by VOXEL_SCALE (16)
            # to properly space blocks in the voxel grid
            # Note: Scrap Mechanic uses different axis mapping than Minecraft
            # MC: X=east, Y=up, Z=south
            # SM: X=right, Y=forward, Z=up
            abs_pos = {
                'x': base_x * VOXEL_SCALE + rotated_pos['x'],
                'y': base_z * VOXEL_SCALE + rotated_pos['z'],  # MC Z -> SM Y
                'z': base_y * VOXEL_SCALE + rotated_pos['y']   # MC Y -> SM Z
            }
            
            if idx < 3 and len(blueprint["bodies"][0]["childs"]) < 2:
                print(f"      Voxel at relative ({rel_pos['x']}, {rel_pos['y']}, {rel_pos['z']}) -> absolute SM ({abs_pos['x']}, {abs_pos['y']}, {abs_pos['z']})")
            
            # Create block entry for blueprint
            # Use the block's rotation for ALL voxels (consistent rotation)
            part = {
                "bounds": voxel.get('bounds', {"x": 1, "y": 1, "z": 1}),
                "shapeId": voxel.get('shapeId', '628b2d61-5ceb-43e9-8334-a4135566df7a'),
                "color": voxel.get('color', '808080'),
                "pos": abs_pos,
                "xaxis": xaxis,  # Use block rotation, not voxel-specific rotation
                "zaxis": zaxis   # Use block rotation, not voxel-specific rotation
            }
            
            blueprint["bodies"][0]["childs"].append(part)
            stats['blocks_added'] += 1
    
    stats['voxels_before_dedup'] = len(blueprint["bodies"][0]["childs"])
    
    # Remove overlapping voxels (same position) - these can crash the game
    print(f"\nRemoving overlapping voxels...")
    blueprint = deduplicate_voxels(blueprint)
    stats['voxels_after_dedup'] = len(blueprint["bodies"][0]["childs"])
    stats['overlapping_voxels_removed'] = stats['voxels_before_dedup'] - stats['voxels_after_dedup']
    
    if stats['overlapping_voxels_removed'] > 0:
        print(f"  Removed {stats['overlapping_voxels_removed']} overlapping voxels ({100*stats['overlapping_voxels_removed']//stats['voxels_before_dedup']}% reduction)")
    else:
        print(f"  No overlapping voxels found")
    
    # Hollow out if requested
    if hollow:
        original_count = len(blueprint["bodies"][0]["childs"])
        print(f"\nHollowing out blueprint...")
        blueprint = hollow_out_blueprint(blueprint)
        new_count = len(blueprint["bodies"][0]["childs"])
        print(f"  Parts reduced: {original_count} -> {new_count} ({100*(1-new_count/original_count):.1f}% reduction)")
    
    # Split into chunks if requested
    blueprint_chunks = []
    if split_chunks:
        chunks_info = split_blueprint_into_chunks(blueprint, max_voxels_per_chunk)
        # Only actually split if we got multiple chunks back
        if len(chunks_info) > 1:
            blueprint_chunks = chunks_info
        else:
            # Single chunk, treat as normal
            blueprint_chunks = [{'blueprint': blueprint, 'chunk_index': (0, 0, 0), 'voxel_count': len(blueprint['bodies'][0]['childs'])}]
    else:
        # No splitting, single blueprint
        blueprint_chunks = [{'blueprint': blueprint, 'chunk_index': (0, 0, 0), 'voxel_count': len(blueprint['bodies'][0]['childs'])}]
    
    # Save each chunk as a separate blueprint
    saved_folders = []
    for chunk_idx, chunk_info in enumerate(blueprint_chunks):
        chunk_blueprint = chunk_info['blueprint']
        chunk_pos = chunk_info['chunk_index']
        
        # Create unique folder for each chunk
        if len(blueprint_chunks) > 1:
            # Multiple chunks - use chunk index in folder name
            chunk_bp_id = str(uuid4())
            chunk_bp_folder = os.path.join(output_dir, chunk_bp_id)
            chunk_name = f"{blueprint_name}_part_{chunk_idx+1}_of_{len(blueprint_chunks)}"
            chunk_desc = f"Part {chunk_idx+1}/{len(blueprint_chunks)} - Chunk ({chunk_pos[0]}, {chunk_pos[1]}, {chunk_pos[2]}) - {schematic_data['width']}x{schematic_data['height']}x{schematic_data['length']}"
        else:
            # Single blueprint
            chunk_bp_folder = bp_folder
            chunk_name = blueprint_name
            chunk_desc = f"Voxel copy of Minecraft schematic - {schematic_data['width']}x{schematic_data['height']}x{schematic_data['length']}"
        
        os.makedirs(chunk_bp_folder, exist_ok=True)
        
        # Write blueprint.json
        blueprint_path = os.path.join(chunk_bp_folder, "blueprint.json")
        try:
            with open(blueprint_path, 'w') as f:
                json.dump(chunk_blueprint, f, separators=(',', ':'))
                f.flush()  # Ensure data is written to OS buffer
                os.fsync(f.fileno())  # Force write to disk
        except Exception as e:
            print(f"Error writing blueprint.json for chunk {chunk_idx+1}: {e}")
            raise
        
        # Write description.json
        desc = {
            "description": chunk_desc,
            "localId": os.path.basename(chunk_bp_folder),
            "name": chunk_name,
            "type": "Blueprint",
            "version": 0
        }
        desc_path = os.path.join(chunk_bp_folder, "description.json")
        try:
            with open(desc_path, 'w') as f:
                json.dump(desc, f, indent=2)
                f.flush()  # Ensure data is written to OS buffer
                os.fsync(f.fileno())  # Force write to disk
        except Exception as e:
            print(f"Error writing description.json for chunk {chunk_idx+1}: {e}")
            raise
        
        # Generate preview image from blueprint parts
        if chunk_idx == 0 or len(blueprint_chunks) <= 5:  # Only generate for first chunk or if few chunks to save time
            print(f"\nGenerating preview image for chunk {chunk_idx+1}...")
        voxel_colors = {}
        for part in chunk_blueprint["bodies"][0]["childs"]:
            pos = part['pos']
            # Convert hex color back to RGB
            color_hex = part['color']
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            voxel_colors[(pos['x'], pos['y'], pos['z'])] = (r, g, b, 255)
        
        generate_preview_image(voxel_colors, chunk_bp_folder)
        saved_folders.append(chunk_bp_folder)
    
    # Print statistics
    print(f"\n{'='*60}")
    print(f"Assembly complete!")
    print(f"{'='*60}")
    print(f"  Total MC blocks processed: {stats['total_blocks']}")
    print(f"  Blocks skipped (missing): {stats['blocks_skipped']}")
    print(f"  Initial voxels placed: {stats['voxels_before_dedup']}")
    print(f"  Overlapping voxels removed: {stats['overlapping_voxels_removed']}")
    print(f"  Voxels after deduplication: {stats['voxels_after_dedup']}")
    if hollow:
        print(f"  Final voxel count (after hollowing): {sum(c['voxel_count'] for c in blueprint_chunks)}")
    
    if len(blueprint_chunks) > 1:
        print(f"\n  Split into {len(blueprint_chunks)} chunks:")
        for i, chunk_info in enumerate(blueprint_chunks):
            print(f"    Chunk {i+1}: {chunk_info['voxel_count']} voxels")
    else:
        print(f"\n  Final blueprint size: {blueprint_chunks[0]['voxel_count']} voxels")
    
    if stats['missing_blueprints']:
        print(f"\n  Missing blueprints ({len(stats['missing_blueprints'])}):")
        for name in sorted(stats['missing_blueprints'])[:10]:
            print(f"    - {name}")
        if len(stats['missing_blueprints']) > 10:
            print(f"    ... and {len(stats['missing_blueprints']) - 10} more")
    
    print(f"\n{'='*60}")
    if len(saved_folders) > 1:
        print(f"Blueprints saved to: {output_dir}")
        print(f"  Created {len(saved_folders)} blueprint chunks")
        for i, folder in enumerate(saved_folders):
            print(f"    Part {i+1}: {os.path.basename(folder)}")
    else:
        print(f"Blueprint saved to: {saved_folders[0]}")
    print(f"{'='*60}")
    
    return saved_folders[0] if len(saved_folders) == 1 else output_dir


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
        help="Path to the folder containing pre-generated block blueprints (optional if using --generate-on-demand)"
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
        default=True,
        help="Hollow out the blueprint to remove interior voxels and reduce part count. This is now the default behavior. Use --no-hollow to disable."
    )
    parser.add_argument(
        "--no-hollow",
        dest="hollow",
        action="store_false",
        help="Disable hollowing (not recommended for large structures)"
    )
    parser.add_argument(
        "--assets", "-a",
        help="Path to Minecraft assets directory for on-demand block generation (e.g., ./MyResourcePack/assets)"
    )
    parser.add_argument(
        "--generate-on-demand",
        action="store_true",
        help="Generate block blueprints on-demand instead of using pre-generated blueprints. Requires --assets."
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Split large blueprints into multiple smaller chunks for easier handling in Scrap Mechanic"
    )
    parser.add_argument(
        "--max-voxels-per-chunk",
        type=int,
        default=50000,
        help="Maximum number of voxels per chunk when splitting (default: 50000)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.isfile(args.schematic):
        print(f"Error: Schematic file not found: {args.schematic}")
        return 1
    
    # Validate blueprint source
    if args.generate_on_demand:
        # On-demand generation requires assets directory
        if not args.assets:
            print(f"Error: --generate-on-demand requires --assets to be specified")
            return 1
        if not os.path.isdir(args.assets):
            print(f"Error: Assets directory not found: {args.assets}")
            return 1
        # Blueprints folder is optional, create empty one if not provided
        if not args.blueprints:
            args.blueprints = "./empty_blueprints"
            os.makedirs(args.blueprints, exist_ok=True)
    else:
        # Traditional mode requires blueprints folder
        if not args.blueprints:
            print(f"Error: --blueprints is required (or use --generate-on-demand with --assets)")
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
    assemble_blueprint(
        schematic_data, 
        args.blueprints, 
        args.output, 
        args.name, 
        hollow=args.hollow,
        assets_dir=args.assets,
        generate_on_demand=args.generate_on_demand,
        split_chunks=args.split,
        max_voxels_per_chunk=args.max_voxels_per_chunk
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
