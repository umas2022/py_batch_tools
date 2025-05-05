
import os
from psd_tools import PSDImage
from PIL import Image

def save_image(image: Image.Image, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    image.save(out_path, 'PNG')

def process_psd_file(file_path, path_in, out_root, merge):
    psd = PSDImage.open(file_path)
    rel_path = os.path.relpath(file_path, start=path_in)
    base_name = os.path.splitext(rel_path)[0]
    out_dir = os.path.join(out_root, os.path.dirname(base_name))

    if merge:
        merged_image = psd.composite()
        out_path = os.path.join(out_root, f'{base_name}.png')
        save_image(merged_image, out_path)
    else:
        for i, layer in enumerate(psd.descendants()):
            if not layer.is_group() and layer.visible:
                layer_image = layer.composite()
                if layer_image:
                    layer_name = layer.name.strip().replace("/", "_").replace("\\", "_")
                    out_path = os.path.join(out_dir, f"{base_name}_layer{i}_{layer_name}.png")
                    save_image(layer_image, out_path)


def psd_to_png(input_json):
    path_in = input_json["path_in"]
    path_out = input_json["path_out"]
    merge = input_json.get("merge", False)

    if os.path.isfile(path_in) and path_in.lower().endswith(".psd"):
        process_psd_file(path_in, path_in, path_out, merge)
    elif os.path.isdir(path_in):
        for root, _, files in os.walk(path_in):
            for file in files:
                if file.lower().endswith(".psd"):
                    full_path = os.path.join(root, file)
                    process_psd_file(full_path, path_in, path_out, merge)
    else:
        print(f"路径无效: {path_in}")
