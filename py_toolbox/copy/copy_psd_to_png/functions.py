import os
import sys
from glob import glob
from psd_tools import PSDImage
from PIL import Image

def psd_to_png(input_json):
    """
    保留完整目录结构导出PSD
    :param input_json: {
        path_in  - 输入文件/目录
        path_out - 输出根目录
        merge    - 是否合并图层
    }
    """
    path_in = input_json['path_in']
    path_out = input_json['path_out']
    merge = input_json['merge']

    if not os.path.exists(path_in):
        raise FileNotFoundError(f'输入路径不存在: {path_in}')

    # 获取所有PSD文件的绝对路径和相对路径
    psd_files = []
    if os.path.isfile(path_in) and path_in.lower().endswith('.psd'):
        rel_path = os.path.relpath(path_in, start=os.path.dirname(path_in))
        psd_files = [(path_in, rel_path)]
    elif os.path.isdir(path_in):
        for root, _, files in os.walk(path_in):
            for file in files:
                if file.lower().endswith('.psd'):
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, start=path_in)
                    psd_files.append((abs_path, rel_path))

    for abs_path, rel_path in psd_files:
        try:
            # 构造输出路径
            if merge:
                # 合并模式：原路径 + _merged.png
                base_name = os.path.splitext(rel_path)[0]
                output_path = os.path.join(path_out, base_name + '_merged.png')
                output_dir = os.path.dirname(output_path)
            else:
                # 独立模式：原路径 + 文件名（不含扩展名）作为目录
                base_name = os.path.splitext(rel_path)[0]
                output_dir = os.path.join(path_out, base_name)
                os.makedirs(output_dir, exist_ok=True)

            # 创建父目录（如果不存在）
            os.makedirs(os.path.dirname(output_path) if merge else output_dir, exist_ok=True)

            if merge:
                _export_merged_psd(abs_path, output_path)
            else:
                _export_psd_layers(abs_path, output_dir)

            print(f'处理完成: {rel_path} -> {output_path if merge else output_dir}')

        except Exception as e:
            print(f'处理失败 [{rel_path}]: {str(e)}')

def _export_psd_layers(psd_path, output_dir):
    """ 导出独立图层 """
    psd = PSDImage.open(psd_path)
    
    def _save_layer(layer, parent_name='', index=1):
        if not layer.visible or layer.kind in ('adjustment', 'solidcolor'):
            return

        layer_name = layer.name.replace('/', '_').strip() or f'Layer_{index}'
        filename = f"{parent_name}_{layer_name}" if parent_name else layer_name
        filename = f"{filename}.png"
        filepath = os.path.join(output_dir, filename)

        if layer.is_group():
            for idx, sub_layer in enumerate(layer, 1):
                _save_layer(sub_layer, filename.split('.')[0], idx)
            return

        if layer.has_pixels():
            image = layer.composite()
            image.save(filepath, 'PNG')

    for idx, layer in enumerate(psd, 1):
        _save_layer(layer, index=idx)

def _export_merged_psd(psd_path, output_path):
    """ 导出合并图像 """
    psd = PSDImage.open(psd_path)

