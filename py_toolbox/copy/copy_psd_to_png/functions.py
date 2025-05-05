
import os
from psd_tools import PSDImage
from PIL import Image

def save_image(image: Image.Image, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    image.save(out_path, 'PNG')

def process_psd_file(file_path, path_in, out_root, merge):
    print(f"\n处理文件: {file_path}")
    psd = PSDImage.open(file_path)
    rel_path = os.path.relpath(file_path, start=path_in)
    base_name = os.path.splitext(rel_path)[0]
    out_dir = os.path.join(out_root, os.path.dirname(base_name))

    if merge:
        print("  -> 合并图层导出...")
        merged_image = psd.composite()
        out_path = os.path.join(out_root, f'{base_name}.png')
        save_image(merged_image, out_path)
        print(f"     已保存: {out_path}")
    else:
        print("  -> 单独导出每个图层...")
        layer_count = 0
        for i, layer in enumerate(psd.descendants()):
            if not layer.is_group() and layer.visible:
                layer_image = layer.composite()
                if layer_image:
                    layer_name = layer.name.strip().replace("/", "_").replace("\\", "_")
                    out_path = os.path.join(out_dir, f"{base_name}_layer{i}_{layer_name}.png")
                    save_image(layer_image, out_path)
                    print(f"     [+] 导出图层: {layer_name} -> {out_path}")
                    layer_count += 1
                else:
                    print(f"     [-] 图层空白: {layer.name}")
            else:
                print(f"     [-] 跳过组或隐藏图层: {layer.name}")
        if layer_count == 0:
            print("     [!] 未导出任何图层（可能是全部隐藏或空）")

def psd_to_png(input_json):
    path_in = input_json["path_in"]
    path_out = input_json["path_out"]
    merge = input_json.get("merge", False)

    print(f"开始处理 PSD 文件\n输入路径: {path_in}\n输出路径: {path_out}\n合并图层: {merge}")
    total_files = 0

    if os.path.isfile(path_in) and path_in.lower().endswith(".psd"):
        process_psd_file(path_in, path_in, path_out, merge)
        total_files = 1
    elif os.path.isdir(path_in):
        for root, _, files in os.walk(path_in):
            for file in files:
                if file.lower().endswith(".psd"):
                    full_path = os.path.join(root, file)
                    process_psd_file(full_path, path_in, path_out, merge)
                    total_files += 1
    else:
        print(f"[X] 无效路径: {path_in}")
        return

    print(f"\n✅ 处理完成，共处理 PSD 文件数: {total_files}")
