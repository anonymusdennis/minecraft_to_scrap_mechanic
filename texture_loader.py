# texture_loader.py
import os
from PIL import Image

# Cache loaded images to avoid reloading
_texture_cache = {}

def load_texture(file_path):
    """Load an image and return a Pillow Image object. Returns None if file doesn't exist."""
    if file_path in _texture_cache:
        return _texture_cache[file_path]
    if not os.path.isfile(file_path):
        print(f"Warning: texture file not found: {file_path}")
        _texture_cache[file_path] = None
        return None
    try:
        img = Image.open(file_path)
        img = img.convert("RGBA")  # ensure RGBA
        _texture_cache[file_path] = img
        return img
    except Exception as e:
        print(f"Warning: failed to load texture {file_path}: {e}")
        _texture_cache[file_path] = None
        return None

def sample_texture(img, uv_coords):
    """
    Sample the color from the image at the given UV coordinates.
    :param img: Pillow Image (RGBA) or None.
    :param uv_coords: (u, v) tuple in [0,1] range (normalized texture coords).
    :return: (r, g, b, a) color tuple, or None if img is None.
    """
    if img is None:
        return None
    width, height = img.size
    if width == 0 or height == 0:
        return None
    # Compute pixel coordinates – note that (0,0) in UV is top-left of the image
    # Clamp UV coordinates to [0, 1] range first
    u = max(0.0, min(1.0, uv_coords[0]))
    v = max(0.0, min(1.0, uv_coords[1]))
    px = int(u * width)
    py = int(v * height)
    # Clamp to image bounds (in case of 1.0 exactly, use last pixel index)
    if px >= width:  px = width - 1
    if py >= height: py = height - 1
    if px < 0: px = 0
    if py < 0: py = 0
    try:
        color = img.getpixel((px, py))
        return color
    except (IndexError, TypeError):
        # Fallback if getpixel fails for any reason
        return None
