# main.py
import argparse, os, shutil
from model_parser import load_model, resolve_model
from voxelizer import voxelize_model
from blueprint_writer import export_blueprint

def main(input_dir, output_dir):
    assets_dir = input_dir  # e.g. "./MyResourcePack/assets"
    mc_models_dir = os.path.join(assets_dir, "minecraft", "models", "block")
    if not os.path.isdir(mc_models_dir):
        print(f"Error: Cannot find models in {mc_models_dir}")
        return
    # Clear output directory if it exists
    if os.path.isdir(output_dir):
        print(f"Clearing output directory: {output_dir}")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    # Loop through block model JSON files
    for filename in os.listdir(mc_models_dir):
        if not filename.endswith(".json"):
            continue
        model_name = filename[:-5]  # drop .json
        model_path = f"minecraft:block/{model_name}"
        try:
            model = load_model(model_path, assets_dir)
        except Exception as e:
            print(f"Skipping {model_name}: {e}")
            continue
        # Ensure model has elements (skip empty ones or purely item models)
        if "elements" not in model or len(model["elements"]) == 0:
            continue
        resolved_elems = resolve_model(model, assets_dir)
        voxel_colors = voxelize_model(resolved_elems, {})
        # If no voxels (empty model), skip
        if len(voxel_colors) == 0:
            continue
        bp_name = model_name
        # Include namespace if not default
        if ":" in model_path:
            bp_name = model_path.split(":",1)[1].replace("block/","").replace("/", "_")
        else:
            bp_name = model_name
        # Export blueprint (pass model_name for material mapping)
        export_blueprint(voxel_colors, output_dir, bp_name, block_name=model_name)
        print(f"Exported {bp_name} to blueprint.")
    print("Conversion complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Minecraft block models to Scrap Mechanic blueprints.")
    parser.add_argument("--input", "-i", required=True, help="Path to the 'assets' directory of the resource pack (e.g. ./MyPack/assets)")
    parser.add_argument("--output", "-o", required=True, help="Output directory for generated blueprints")
    args = parser.parse_args()
    main(args.input, args.output)
