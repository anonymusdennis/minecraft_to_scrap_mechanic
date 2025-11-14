# blueprint_writer.py
import os, json
from uuid import uuid4
from PIL import Image

# Scrap Mechanic shape IDs for different materials
SHAPE_IDS = {
    "wood2": "1fc74a28-addb-451a-878d-c3c605d63811",
    "wood2": "1897ee42-0291-43e4-9645-8c5a5d310398",
    "wood2": "061b5d4b-0a6a-4212-b0ae-9e9681f1cbfb",
    "scrapmetal": "1f7ac0bb-ad45-4246-9817-59bdf7f7ab39",
    "metal2": "1016cafc-9f6b-40c9-8713-9019d399783f",
    "metal3": "c0dfdea5-a39d-433a-b94a-299345a5df46",
    "scrapstone": "30a2288b-e88e-4a92-a916-1edbfc2b2dac",
    "concrete2": "ff234e42-5da4-43cc-8893-940547c97882",
    "concrete3": "e281599c-2343-4c86-886e-b2c1444e8810",
    "crackedconcrete": "f5ceb7e3-5576-41d2-82d2-29860cf6e20e",
    "concretetiles": "cd0eff89-b693-40ee-bd4c-3500b23df44e",
    "metalbricks": "220b201e-aa40-4995-96c8-e6007af160de",
    "beam": "25a5ffe7-11b1-4d3e-8d7a-48129cbaf05e",
    "bubblewrap": "f406bf6e-9fd5-4aa0-97c1-0b3c2118198e",
    "plastic": "628b2d61-5ceb-43e9-8334-a4135566df7a",
    "insulation": "9be6047c-3d44-44db-b4b9-9bcf8a9aab20",
    "drywall": "b145d9ae-4966-4af6-9497-8fca33f9aee3",
    "carpet": "febce8a6-6c05-4e5d-803b-dfa930286944",
    "plasticwall": "e981c337-1c8a-449c-8602-1dd990cbba3a",
    "metalnet": "4aa2a6f0-65a4-42e3-bf96-7dec62570e0b",
    "crossnet": "3d0b7a6e-5b40-474c-bbaf-efaa54890e6a",
    "tryponet": "ea6864db-bb4f-4a89-b9ec-977849b6713a",
    "stripednet": "a479066d-4b03-46b5-8437-e99fec3f43ee",
    "squarenet": "b4fa180c-2111-4339-b6fd-aed900b57093",
    "restroom": "920b40c8-6dfc-42e7-84e1-d7e7e73128f6",
    "treadplate": "f7d4bfed-1093-49b9-be32-394c872a1ef4",
    "warehousefloor": "3e3242e4-1791-4f70-8d1d-0ae9ba3ee94c",
    "wornmetal": "d740a27d-cc0f-4866-9e07-6a5c516ad719",
    "spaceshipfloor": "4ad97d49-c8a5-47f3-ace3-d56ba3affe50",
    "sand": "c56700d9-bbe5-4b17-95ed-cef05bd8be1b",
    "armoredglass": "b5ee5539-75a2-4fef-873b-ef7c9398b3f5",  # Glass for transparent blocks
}

# Default shape ID (plastic)
DEFAULT_SHAPE_ID = SHAPE_IDS["plastic"]
GLASS_SHAPE_ID = SHAPE_IDS["armoredglass"]

def get_shape_id_for_block(block_name):
    """
    Map Minecraft block names to appropriate Scrap Mechanic materials.
    Returns a shapeId string.
    """
    block_lower = block_name.lower()
    
    # Wood blocks
    if any(wood in block_lower for wood in ["oak", "birch", "spruce", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "crimson", "warped"]):
        if "planks" in block_lower or "log" in block_lower or "wood" in block_lower:
            return SHAPE_IDS["wood2"]
        elif "door" in block_lower or "trapdoor" in block_lower:
            return SHAPE_IDS["wood2"]
        elif "stairs" in block_lower or "slab" in block_lower:
            return SHAPE_IDS["wood2"]
        return SHAPE_IDS["wood2"]
    
    # Default fallback
    return DEFAULT_SHAPE_ID

def rgba_to_hex(rgb):
    """Convert an (r,g,b[,a]) tuple to a Scrap Mechanic hex color string."""
    r, g, b = rgb[0], rgb[1], rgb[2]
    # Scrap Mechanic expects uppercase hex with no prefix
    return f"{r:02x}{g:02x}{b:02x}".upper()

def hollow_out_voxels(voxel_colors):
    """
    Remove interior voxels from a voxel model, keeping only the outer shell.
    This significantly reduces the number of parts for large structures.
    
    :param voxel_colors: dict of (x,y,z) -> (R,G,B,A)
    :return: dict of (x,y,z) -> (R,G,B,A) with interior voxels removed
    """
    if len(voxel_colors) == 0:
        return voxel_colors
    
    # A voxel is interior if all 6 neighbors exist
    hollowed = {}
    
    for pos, color in voxel_colors.items():
        x, y, z = pos
        
        # Check all 6 neighbors
        neighbors = [
            (x+1, y, z), (x-1, y, z),  # X neighbors
            (x, y+1, z), (x, y-1, z),  # Y neighbors
            (x, y, z+1), (x, y, z-1)   # Z neighbors
        ]
        
        # If any neighbor is missing, this is a surface voxel
        is_surface = False
        for neighbor in neighbors:
            if neighbor not in voxel_colors:
                is_surface = True
                break
        
        if is_surface:
            hollowed[pos] = color
    
    return hollowed

def generate_preview_image(voxel_colors, bp_folder, size=128):
    """
    Generate a preview image (icon.png) for the blueprint.
    Creates an isometric-style view of the voxel model.
    """
    if len(voxel_colors) == 0:
        return
    
    # Find bounding box
    min_x = min(x for x, y, z in voxel_colors.keys())
    max_x = max(x for x, y, z in voxel_colors.keys())
    min_y = min(y for x, y, z in voxel_colors.keys())
    max_y = max(y for x, y, z in voxel_colors.keys())
    min_z = min(z for x, y, z in voxel_colors.keys())
    max_z = max(z for x, y, z in voxel_colors.keys())
    
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    depth = max_z - min_z + 1
    max_dim = max(width, height, depth)
    
    if max_dim == 0:
        return
    
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    pixels = img.load()
    
    # Scale factor
    scale = (size * 0.8) / max_dim
    
    # Isometric projection: x' = (x - z) * scale, y' = (y + (x + z) / 2) * scale
    center_x, center_y = size // 2, size // 2
    
    # Sort voxels by depth (z + x + y) for proper rendering order
    sorted_voxels = sorted(voxel_colors.items(), key=lambda v: v[0][2] + v[0][0] + v[0][1])
    
    for (x, y, z), color in sorted_voxels:
        # Normalize coordinates
        nx = (x - min_x) - width / 2
        ny = (y - min_y) - height / 2
        nz = (z - min_z) - depth / 2
        
        # Isometric projection
        px = int(center_x + (nx - nz) * scale)
        py = int(center_y + (ny + (nx + nz) * 0.5) * scale)
        
        # Draw voxel as a small square
        voxel_size = max(2, int(scale * 0.8))
        for dx in range(-voxel_size//2, voxel_size//2 + 1):
            for dy in range(-voxel_size//2, voxel_size//2 + 1):
                px2 = px + dx
                py2 = py + dy
                if 0 <= px2 < size and 0 <= py2 < size:
                    # Blend with existing pixels
                    existing = pixels[px2, py2]
                    if len(color) > 3:
                        alpha = color[3] / 255.0
                        r = int(color[0] * alpha + existing[0] * (1 - alpha))
                        g = int(color[1] * alpha + existing[1] * (1 - alpha))
                        b = int(color[2] * alpha + existing[2] * (1 - alpha))
                        a = min(255, int(existing[3] + color[3] * (1 - existing[3] / 255.0)))
                    else:
                        r, g, b = color[0], color[1], color[2]
                        a = 255
                    pixels[px2, py2] = (r, g, b, a)
    
    # Save preview image
    icon_path = os.path.join(bp_folder, "icon.png")
    img.save(icon_path, 'PNG')

def export_blueprint(voxel_colors, output_dir, blueprint_name, block_name=None, hollow=False):
    """
    Create a Scrap Mechanic blueprint from voxel data.
    :param voxel_colors: dict of (x,y,z) -> (R,G,B,A)
    :param output_dir: directory to create the blueprint folder in
    :param blueprint_name: name to use for the blueprint (for description.json)
    :param block_name: Minecraft block name for material mapping (defaults to blueprint_name)
    :param hollow: if True, hollow out the interior voxels to reduce part count
    """
    if block_name is None:
        block_name = blueprint_name
    
    # Hollow out if requested
    if hollow:
        original_count = len(voxel_colors)
        voxel_colors = hollow_out_voxels(voxel_colors)
        print(f"  Hollowed: {original_count} -> {len(voxel_colors)} voxels ({100*(1-len(voxel_colors)/original_count):.1f}% reduction)")
    # Generate unique folder name using UUID to avoid collisions
    bp_id = str(uuid4())
    bp_folder = os.path.join(output_dir, bp_id)
    os.makedirs(bp_folder, exist_ok=True)
    # Construct blueprint data structure
    blueprint = {
        "bodies": [
            {"childs": []}
        ],
        "version": 4
    }
    # Get the appropriate material for this block type
    base_shape_id = get_shape_id_for_block(block_name)
    
    for (x, y, z), color in voxel_colors.items():
        # Check if transparent (alpha < 128) - use glass for transparent blocks
        is_transparent = len(color) > 3 and color[3] < 128
        if is_transparent and color[3] == 0:
            continue  # Skip fully transparent voxels
        
        # Use glass for transparent blocks, mapped material for others
        shape_id = GLASS_SHAPE_ID if is_transparent else base_shape_id
        
        part = {
            "bounds": {"x": 1, "y": 1, "z": 1},  # Each voxel is 1x1x1
            "shapeId": shape_id,
            "color": rgba_to_hex(color),  # Color as hex string
            "pos": {"x": x, "y": z, "z": y},  # note: pos.y = z index, pos.z = vertical (y index)
            "xaxis": 1,
            "zaxis": 3
        }
        blueprint["bodies"][0]["childs"].append(part)
    # Write blueprint.json (minified like Scrap Mechanic format)
    blueprint_path = os.path.join(bp_folder, "blueprint.json")
    try:
        with open(blueprint_path, 'w') as f:
            json.dump(blueprint, f, separators=(',', ':'))
            f.flush()  # Ensure data is written to OS buffer
            os.fsync(f.fileno())  # Force write to disk
    except Exception as e:
        print(f"Error writing blueprint.json: {e}")
        raise
    # Write description.json matching Scrap Mechanic format
    desc = {
        "description": f"Converted from Minecraft model {blueprint_name}",
        "localId": bp_id,  # Use the same UUID as the folder name
        "name": blueprint_name,
        "type": "Blueprint",
        "version": 0
    }
    desc_path = os.path.join(bp_folder, "description.json")
    try:
        with open(desc_path, 'w') as f:
            json.dump(desc, f, indent=2)
            f.flush()  # Ensure data is written to OS buffer
            os.fsync(f.fileno())  # Force write to disk
    except Exception as e:
        print(f"Error writing description.json: {e}")
        raise
    
    # Generate preview image (icon.png)
    generate_preview_image(voxel_colors, bp_folder)
