import os
import hashlib
from PIL import Image
import shutil


def remove_duplicate_images(input_json):
    """
    遍历指定目录下的图片，根据 if_cut 参数处理重复图片。
    如果 if_cut 为 True，将所有重复图片剪切到指定目录；
    如果 if_cut 为 False，保留第一张重复图片，删除其他重复图片。

    参数:
        input_json (dict): 包含以下键的字典：
            - path_in (str): 目标目录路径。
            - if_cut (bool): 是否剪切重复图片，默认为 False 表示删除。
            - cut_path (str): 若 if_cut 为 True，指定剪切图片的目标路径。

    返回:
        None
    """
    # 解析输入参数
    path_in = input_json.get("path_in")
    if_cut = input_json.get("if_cut", False)
    cut_path = input_json.get("cut_path")

    # 检查目录是否存在
    if not os.path.exists(path_in):
        print(f"目录不存在: {path_in}")
        return

    if if_cut and not os.path.exists(cut_path):
        os.makedirs(cut_path)

    # 用于存储已处理图片的尺寸和哈希值以及对应的文件路径列表
    size_hash_dict = {}

    # 递归遍历目录及其子文件夹
    for root, dirs, files in os.walk(path_in):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                # 检查文件是否为图片
                with Image.open(file_path) as img:
                    width, height = img.size
                    img_hash = hashlib.sha256(img.tobytes()).hexdigest()
                    size_hash = (width, height, img_hash)

                    if size_hash in size_hash_dict:
                        # 如果是重复图片，添加到对应的文件路径列表
                        size_hash_dict[size_hash].append(file_path)
                    else:
                        # 记录当前图片的尺寸和哈希值以及文件路径列表
                        size_hash_dict[size_hash] = [file_path]
            except (IOError, OSError):
                # 非图片文件或无法打开的文件，跳过
                continue

    # 处理重复图片
    for size_hash, file_paths in size_hash_dict.items():
        if len(file_paths) > 1:  # 如果有重复图片
            if if_cut:
                # 将所有重复图片剪切到指定目录
                for file_path in file_paths:
                    # 计算相对路径
                    relative_path = os.path.relpath(os.path.dirname(file_path), path_in)
                    target_dir = os.path.join(cut_path, relative_path)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    target_path = os.path.join(target_dir, os.path.basename(file_path))
                    shutil.move(file_path, target_path)
                    print(f"已剪切重复图片到: {target_path}")
            else:
                # 保留第一张图片，删除其他重复图片
                for file_path in file_paths[1:]:
                    os.remove(file_path)
                    print(f"已删除重复图片: {file_path}")


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        "path_in": r"D:\test\images",
        "if_cut": False,
        "cut_path": r"D:\test\duplicates",
    }
    remove_duplicate_images(config)