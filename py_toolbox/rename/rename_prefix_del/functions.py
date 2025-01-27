import os

def remove_prefix(input_json):
    """
    遍历指定目录下的文件和/或目录，并删除其名称中的特定前缀。

    参数:
        input_json (dict): 包含以下键的字典：
            - path_in (str): 目标目录路径。
            - prefix (str): 要删除的文件名前缀。
            - target (str): 指定操作对象，可选值为 "file"（仅文件）、"dir"（仅目录）或 "all"（文件和目录），默认为 "all"。
    返回:
        None
    """
    # 解析输入参数
    path_in = input_json.get("path_in")
    prefix = input_json.get("prefix")
    target = input_json.get("target", "all")

    # 检查目录是否存在
    if not os.path.exists(path_in):
        print(f"目录不存在: {path_in}")
        return

    # 递归遍历目录及其子文件夹
    for root, dirs, files in os.walk(path_in, topdown=False):
        if target in ["dir", "all"]:
            for dir_name in dirs:
                if dir_name.startswith(prefix):
                    # 构建旧目录的完整路径
                    old_dir_path = os.path.join(root, dir_name)
                    # 构建新目录名
                    new_dir_name = dir_name[len(prefix):]
                    # 构建新目录的完整路径
                    new_dir_path = os.path.join(root, new_dir_name)

                    try:
                        # 重命名目录
                        os.rename(old_dir_path, new_dir_path)
                        print(f"已重命名目录: {old_dir_path} -> {new_dir_path}")
                    except Exception as e:
                        print(f"重命名目录失败: {old_dir_path}, 错误: {e}")

        if target in ["file", "all"]:
            for filename in files:
                if filename.startswith(prefix):
                    # 构建旧文件的完整路径
                    old_file_path = os.path.join(root, filename)
                    # 构建新文件名
                    new_filename = filename[len(prefix):]
                    # 构建新文件的完整路径
                    new_file_path = os.path.join(root, new_filename)

                    try:
                        # 重命名文件
                        os.rename(old_file_path, new_file_path)
                        print(f"已重命名文件: {old_file_path} -> {new_file_path}")
                    except Exception as e:
                        print(f"重命名文件失败: {old_file_path}, 错误: {e}")
