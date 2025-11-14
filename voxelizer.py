# voxelizer.py
import math
from collections import deque
from texture_loader import load_texture, sample_texture

def voxelize_model(resolved_elements, texture_cache):
    """
    Voxelize the given model elements at appropriate resolution.
    :param resolved_elements: List of model elements (from resolve_model) with 'from', 'to', 'faces'.
    :param texture_cache: A dict to store loaded textures (to avoid reloading).
    :return: A dict mapping voxel (x,y,z) -> RGBA color.
    """
    # Determine grid resolution (N) based on largest texture size used
    N = 16
    max_tex_size = 16
    # First, find max texture dimension among all faces to set grid resolution
    for elem in resolved_elements:
        for face, face_data in elem["faces"].items():
            tex_file = face_data.get("texture_file")
            if tex_file is None:
                continue  # Skip faces with missing textures
            img = load_texture(tex_file)
            if img is None:
                # Mark this face as invalid for later
                face_data["texture_file"] = None
                continue
            # Update max texture dimension
            w, h = img.size
            if w > max_tex_size: max_tex_size = w
            if h > max_tex_size: max_tex_size = h
    if max_tex_size > 16:
        N = max_tex_size  # use the higher resolution for grid
    # 3D grid to mark filled voxels
    filled = [[[False for _ in range(N)] for _ in range(N)] for _ in range(N)]
    # Fill grid for each element
    for elem in resolved_elements:
        # Pre-calc element bounds in voxel indices
        fx, fy, fz = elem["from"]; tx, ty, tz = elem["to"]
        # If element has rotation, we'll need to test each voxel in its AABB
        rotated = False
        rot_origin = None
        rot_axis = None
        rot_angle = None
        sin_a = cos_a = 0
        if "rotation" in elem:
            rot = elem["rotation"]
            rot_origin = tuple(rot.get("origin", (0,0,0)))
            rot_axis = rot.get("axis", None)  # 'x','y', or 'z'
            rot_angle = rot.get("angle", 0)
            if rot_axis and rot_angle and abs(rot_angle) > 1e-6:
                rotated = True
                # Convert angle to radians
                theta = math.radians(rot_angle)
                sin_a = math.sin(theta); cos_a = math.cos(theta)
        # Determine voxel index range to consider for this element
        min_x = max(0, math.floor(min(fx, tx)))
        max_x = min(N, math.ceil(max(fx, tx)))
        min_y = max(0, math.floor(min(fy, ty)))
        max_y = min(N, math.ceil(max(fy, ty)))
        min_z = max(0, math.floor(min(fz, tz)))
        max_z = min(N, math.ceil(max(fz, tz)))
        for i in range(min_x, max_x):
            for j in range(min_y, max_y):
                for k in range(min_z, max_z):
                    if rotated:
                        # Transform voxel center back to element's local coordinates (subtract origin, inverse rotate, add origin back)
                        # Voxel center in world coords:
                        wx = i + 0.5; wy = j + 0.5; wz = k + 0.5
                        ox, oy, oz = rot_origin
                        # translate to origin
                        tx_ = wx - ox; ty_ = wy - oy; tz_ = wz - oz
                        if rot_axis == 'x':
                            # rotate around X-axis
                            x_ = tx_
                            y_ = ty_ * cos_a + tz_ * sin_a
                            z_ = -ty_ * sin_a + tz_ * cos_a
                        elif rot_axis == 'y':
                            x_ = tx_ * cos_a + tz_ * sin_a
                            y_ = ty_
                            z_ = -tx_ * sin_a + tz_ * cos_a
                        elif rot_axis == 'z':
                            x_ = tx_ * cos_a - ty_ * sin_a
                            y_ = tx_ * sin_a + ty_ * cos_a
                            z_ = tz_
                        # translate back from origin
                        x_local = x_ + ox; y_local = y_ + oy; z_local = z_ + oz
                        # Check if local point is inside the unrotated cuboid
                        if x_local < fx or x_local >= tx or \
                           y_local < fy or y_local >= ty or \
                           z_local < fz or z_local >= tz:
                            continue  # this voxel center is outside the element
                        filled[i][j][k] = True
                    else:
                        # Axis-aligned element
                        if i + 0.5 < fx or i + 0.5 >= tx: 
                            continue
                        if j + 0.5 < fy or j + 0.5 >= ty: 
                            continue
                        if k + 0.5 < fz or k + 0.5 >= tz: 
                            continue
                        filled[i][j][k] = True
    
    # Note: Individual block blueprints are now generated as solid (not hollowed)
    # This allows proper assembly where adjacent blocks can merge and then be 
    # hollowed out as a complete structure in the schematic assembler
    # Determine voxel colors
    voxel_colors = {}
    for i in range(0, N):
        for j in range(0, N):
            for k in range(0, N):
                if not filled[i][j][k]:
                    continue
                # Determine the color of this voxel
                color = None
                # Priority: up face color > side face > down face
                face_order = ["up","north","south","east","west","down"]
                for face in face_order:
                    # Check if this face of voxel is exposed
                    di, dj, dk = 0,0,0
                    if face == "up":    dj = 1
                    if face == "down":  dj = -1
                    if face == "north": dk = -1
                    if face == "south": dk = 1
                    if face == "west":  di = -1
                    if face == "east":  di = 1
                    neighbor = (i+di, j+dj, k+dk)
                    if 0 <= neighbor[0] < N and 0 <= neighbor[1] < N and 0 <= neighbor[2] < N:
                        if filled[neighbor[0]][neighbor[1]][neighbor[2]]:
                            continue  # neighbor filled, not an exposed face
                    # Now find which element's face covers this voxel on the given side
                    # Use a more lenient check: if the voxel is near the face boundary and within the element bounds
                    face_data = None  # Initialize before loop
                    elem_bounds = None  # Store element bounds for UV calculation
                    for elem in resolved_elements:
                        fx, fy, fz = elem["from"]; tx, ty, tz = elem["to"]
                        voxel_center_x, voxel_center_y, voxel_center_z = i + 0.5, j + 0.5, k + 0.5
                        
                        # Check if voxel center is within element bounds
                        if not (fx <= voxel_center_x < tx and fy <= voxel_center_y < ty and fz <= voxel_center_z < tz):
                            continue
                            
                        if face == "up":
                            # Check if voxel is near the top face (ty)
                            if abs(voxel_center_y - ty) < 0.6:  # More lenient threshold
                                if fx <= voxel_center_x < tx and fz <= voxel_center_z < tz:
                                    face_data = elem["faces"].get("up")
                                    if face_data:
                                        elem_bounds = (fx, fy, fz, tx, ty, tz)
                                        break
                        elif face == "down":
                            if abs(voxel_center_y - fy) < 0.6:
                                if fx <= voxel_center_x < tx and fz <= voxel_center_z < tz:
                                    face_data = elem["faces"].get("down")
                                    if face_data:
                                        elem_bounds = (fx, fy, fz, tx, ty, tz)
                                        break
                        elif face == "north":
                            if abs(voxel_center_z - fz) < 0.6:
                                if fx <= voxel_center_x < tx and fy <= voxel_center_y < ty:
                                    face_data = elem["faces"].get("north")
                                    if face_data:
                                        elem_bounds = (fx, fy, fz, tx, ty, tz)
                                        break
                        elif face == "south":
                            if abs(voxel_center_z - tz) < 0.6:
                                if fx <= voxel_center_x < tx and fy <= voxel_center_y < ty:
                                    face_data = elem["faces"].get("south")
                                    if face_data:
                                        elem_bounds = (fx, fy, fz, tx, ty, tz)
                                        break
                        elif face == "west":
                            if abs(voxel_center_x - fx) < 0.6:
                                if fz <= voxel_center_z < tz and fy <= voxel_center_y < ty:
                                    face_data = elem["faces"].get("west")
                                    if face_data:
                                        elem_bounds = (fx, fy, fz, tx, ty, tz)
                                        break
                        elif face == "east":
                            if abs(voxel_center_x - tx) < 0.6:
                                if fz <= voxel_center_z < tz and fy <= voxel_center_y < ty:
                                    face_data = elem["faces"].get("east")
                                    if face_data:
                                        elem_bounds = (fx, fy, fz, tx, ty, tz)
                                        break
                    
                    if face_data and elem_bounds:
                        fx, fy, fz, tx, ty, tz = elem_bounds
                        tex_file = face_data.get("texture_file")
                        if tex_file is None:
                            continue  # Skip faces with missing textures
                        img = load_texture(tex_file)
                        if img is None:
                            continue  # Skip if texture couldn't be loaded
                        # Determine UV of voxel center relative to that face
                        u1, v1, u2, v2 = face_data.get("uv", [0,0,16,16])
                        # Normalize UV coordinates (0-1)
                        # Note: u corresponds to horizontal axis of face texture, v to vertical axis.
                        if face in ("north","south","east","west"):
                            # Vertical faces: horizontal = x (or z for east/west), vertical = y
                            # For north/south: x-axis corresponds to u, y-axis corresponds to v (top is v=0).
                            # For east/west: z-axis corresponds to u (since east/west faces run north-south horizontally), y-axis to v.
                            if face == "north":
                                # North face: u goes from west to east (fx to tx)
                                u_frac = (i + 0.5 - fx) / (tx - fx) if tx != fx else 0
                            elif face == "south":
                                # South face: u goes from east to west (mirrored), so flip u
                                u_frac = 1.0 - ((i + 0.5 - fx) / (tx - fx) if tx != fx else 0)
                            elif face == "west":
                                # West face: u goes from north to south (fz to tz)
                                u_frac = (k + 0.5 - fz) / (tz - fz) if tz != fz else 0
                            else:  # east
                                # East face: u goes from south to north (mirrored), so flip u
                                u_frac = 1.0 - ((k + 0.5 - fz) / (tz - fz) if tz != fz else 0)
                            # vertical frac: top of block = v=0
                            v_frac = (ty - (j + 0.5)) / (ty - fy) if ty != fy else 0
                        else:
                            # Horizontal faces (up/down): horizontal = x, vertical = z (north-> top or bottom of texture)
                            u_frac = (i + 0.5 - fx) / (tx - fx) if tx != fx else 0
                            if face == "up":
                                # north side of face = v=0
                                v_frac = (k + 0.5 - fz) / (tz - fz) if tz != fz else 0
                            else:  # down face, likely rotated 180 by default
                                # for down, north edge corresponds to top of texture as well (assuming no rotation or handled via face rotation)
                                v_frac = (tz - (k + 0.5)) / (tz - fz) if tz != fz else 0
                        # Apply face-specific 90-degree rotation if any
                        rot = face_data.get("rotation", 0)
                        if rot == 90:
                            # 90 deg: swap axes, u becomes 1-v_orig, v becomes u_orig
                            orig_u = u_frac; orig_v = v_frac
                            u_frac = 1.0 - orig_v
                            v_frac = orig_u
                        elif rot == 180:
                            orig_u = u_frac; orig_v = v_frac
                            u_frac = 1.0 - orig_u
                            v_frac = 1.0 - orig_v
                        elif rot == 270:
                            orig_u = u_frac; orig_v = v_frac
                            u_frac = orig_v
                            v_frac = 1.0 - orig_u
                        # Now map into the face's UV rectangle:
                        u_norm = (u1 + u_frac * (u2 - u1)) / 16.0
                        v_norm = (v1 + v_frac * (v2 - v1)) / 16.0
                        # Sample the texture
                        sampled_color = sample_texture(img, (u_norm, v_norm))
                        if sampled_color is not None:
                            color = sampled_color
                            break
                    if color is not None:  # if we found a face and got a valid color
                        break
                if color is None:
                    # No valid texture found for this voxel - use default gray color
                    color = (128, 128, 128, 255)  # Default gray
                voxel_colors[(i, j, k)] = color
    return voxel_colors
