import os
import shutil


def remove_difference(input_json):
    """
    以path_base目录为基准，根据target参数删除path_del目录中多余的文件、目录或两者。

    参数:
        input_json (dict): 包含以下键的字典：
            - path_base (str): 基准目录路径。
            - path_del (str): 需要删除多余文件或目录的目录路径。
            - target (str): 目标类型，可选值为 "file"、"dir" 或 "all"。

    返回:
        None
    """
    # 解析输入参数
    path_base = input_json.get("path_base")
    path_del = input_json.get("path_del")
    target = input_json.get("target", "all")

    # 检查基准目录和要处理的目录是否存在
    if not os.path.exists(path_base):
        print(f"基准目录不存在: {path_base}")
        return
    if not os.path.exists(path_del):
        print(f"要处理的目录不存在: {path_del}")
        return

    # 获取基准目录下所有文件和目录的相对路径
    base_files = set()
    base_dirs = set()
    for root, dirs, files in os.walk(path_base):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), path_base)
            base_files.add(relative_path)
        for d in dirs:
            relative_path = os.path.relpath(os.path.join(root, d), path_base)
            base_dirs.add(relative_path)

    # 遍历要处理的目录下的所有文件和目录
    for root, dirs, files in os.walk(path_del, topdown=False):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), path_del)
            if target in ["file", "all"] and relative_path not in base_files:
                file_to_delete = os.path.join(root, file)
                try:
                    os.remove(file_to_delete)
                    print(f"已删除文件: {file_to_delete}")
                except Exception as e:
                    print(f"删除文件失败: {file_to_delete}, 错误: {e}")
        for d in dirs:
            relative_path = os.path.relpath(os.path.join(root, d), path_del)
            if target in ["dir", "all"] and relative_path not in base_dirs:
                dir_to_delete = os.path.join(root, d)
                try:
                    shutil.rmtree(dir_to_delete)
                    print(f"已删除目录: {dir_to_delete}")
                except Exception as e:
                    print(f"删除目录失败: {dir_to_delete}, 错误: {e}")


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        "path_base": r"D:\test\base",
        "path_del": r"D:\test\delete",
        "target": "all",
    }
    remove_difference(config)