# model_parser.py
import os, json

# Cache for loaded models to avoid re-parsing
_model_cache = {}

def load_model(model_path, base_dir):
    """
    Load and resolve a Minecraft model JSON (including parent inheritance).
    :param model_path: Model path in 'namespace:path' format or relative path.
    :param base_dir: Base directory of assets (e.g. ".../assets").
    :return: Resolved model dictionary with 'elements' and 'textures'.
    """
    # Determine namespace and path
    if ":" in model_path:
        namespace, path = model_path.split(":", 1)
    else:
        namespace, path = "minecraft", model_path
    # Construct filesystem path
    model_file = os.path.join(base_dir, namespace, "models", f"{path}.json")
    if not os.path.isfile(model_file):
        raise FileNotFoundError(f"Model file not found: {model_file}")
    # Return from cache if already loaded
    if model_file in _model_cache:
        return _model_cache[model_file]
    with open(model_file, 'r') as f:
        data = json.load(f)
    model = {}
    # Resolve parent model first, if present
    if "parent" in data:
        parent_path = data["parent"]
        parent_model = load_model(parent_path, base_dir)  # recursive load
        # Start with a copy of parent model's elements and textures
        model["elements"] = [elem.copy() for elem in parent_model.get("elements", [])]
        # Deep-copy faces sub-dicts to avoid reference issues
        for elem in model["elements"]:
            elem["faces"] = {face: face_data.copy() for face, face_data in elem.get("faces", {}).items()}
        model["textures"] = parent_model.get("textures", {}).copy()
    else:
        model["elements"] = []
        model["textures"] = {}
    # Override/extend textures with child’s textures
    if "textures" in data:
        # In model JSON, values like "block/stone" mean namespace "minecraft" by default
        for key, tex in data["textures"].items():
            # Normalize keys: remove leading # if present (non-standard but some models use it)
            normalized_key = key[1:] if key.startswith("#") else key
            
            if tex.startswith("#"):
                # Texture variable reference - keep as-is, don't add namespace
                model["textures"][normalized_key] = tex
            elif ":" in tex:
                # Already has namespace
                model["textures"][normalized_key] = tex
            else:
                # No namespace, default to "minecraft"
                model["textures"][normalized_key] = "minecraft:" + tex
    # If the child defines elements, replace the inherited ones
    if "elements" in data:
        model["elements"] = data["elements"]
    # Store in cache
    _model_cache[model_file] = model
    return model

def resolve_model(model, base_dir):
    """
    Given a loaded model dict (with elements and texture variables), 
    resolve texture variables to actual images (file paths).
    Returns a new dict with resolved 'elements'.
    """
    resolved_elements = []
    textures = model.get("textures", {})
    for elem in model.get("elements", []):
        # Copy element's basic properties
        res_elem = {
            "from": elem["from"][:],  # copy lists
            "to": elem["to"][:]
        }
        # Rotation (if any)
        if "rotation" in elem:
            res_elem["rotation"] = elem["rotation"].copy()
        if "shade" in elem:
            res_elem["shade"] = elem["shade"]
        res_faces = {}
        for face, face_data in elem.get("faces", {}).items():
            # Resolve the texture reference (strip leading '#' and find actual path)
            tex_var = face_data.get("texture")
            if tex_var is None:
                continue
            
            # Handle custom double-hash references (##variable -> #variable)
            if tex_var.startswith("##"):
                tex_var = "#" + tex_var[2:]
            
            if tex_var.startswith("#"):
                tex_key = tex_var[1:]
                if tex_key in textures:
                    tex_ref = textures[tex_key]
                    # Handle recursive texture variable references (e.g., "torch": "#torch")
                    # Resolve up to 10 levels deep to avoid infinite loops
                    depth = 0
                    while tex_ref.startswith("#") and depth < 10:
                        inner_key = tex_ref[1:]
                        if inner_key in textures:
                            tex_ref = textures[inner_key]
                            depth += 1
                        else:
                            break
                    # After resolving, check if we still have an unresolved reference
                    if tex_ref.startswith("#"):
                        # Still unresolved after recursion
                        unresolved_key = tex_ref[1:]
                        # Special case: "missing" is intentionally used for hidden/culled faces
                        if unresolved_key != "missing":
                            print(f"Warning: texture variable '{unresolved_key}' not found in model textures, trying as direct path")
                        tex_ref = unresolved_key
                else:
                    # Texture variable not found - try using the key name as a direct texture path
                    # This handles cases like "torch" variable that should map to "block/torch"
                    # Special case: "missing" is intentionally used for hidden/culled faces
                    if tex_key != "missing":
                        print(f"Warning: texture variable '{tex_key}' not found in model textures, trying as direct path")
                    tex_ref = tex_key  # Fallback to using the key name directly
            else:
                tex_ref = tex_var
            # Determine texture file path
            if ":" in tex_ref:
                ns, tex_path = tex_ref.split(":", 1)
            else:
                ns, tex_path = "minecraft", tex_ref
            # If tex_path doesn't have a folder, assume it's under 'block/'
            if "/" not in tex_path:
                tex_path = f"block/{tex_path}"
            # Textures might omit the '.png' in JSON; we ensure it ends with .png
            if not tex_path.endswith(".png"):
                tex_path = f"{tex_path}.png"
            tex_file = os.path.join(base_dir, ns, "textures", tex_path.replace("/", os.sep))
            res_face = {
                "texture_file": tex_file,
            }
            # UV mapping (if provided)
            if "uv" in face_data:
                # Ensure we have a list of 4 floats [u1, v1, u2, v2]
                res_face["uv"] = face_data["uv"][:]
            # Texture rotation (if any, 0/90/180/270)
            if "rotation" in face_data:
                res_face["rotation"] = face_data["rotation"]
            res_faces[face] = res_face
        res_elem["faces"] = res_faces
        resolved_elements.append(res_elem)
    return resolved_elements
