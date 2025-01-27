import os
import shutil


def remove_keyword(input_json):
    """
    根据 target 参数删除指定目录下及其所有子文件夹中包含关键字的文件、目录或两者。

    参数:
        input_json (dict): 包含以下键的字典：
            - path_in (str): 目标目录路径。
            - key_world (str): 要匹配的关键字。
            - target (str): 目标类型，可选值为 "file"、"dir" 或 "all"。

    返回:
        None
    """
    # 解析输入参数
    path_in = input_json.get("path_in")
    keyword = input_json.get("key_world")
    target = input_json.get("target", "all")

    # 检查目录是否存在
    if not os.path.exists(path_in):
        print(f"目录不存在: {path_in}")
        return

    # 递归遍历目录及其子文件夹
    for root, dirs, files in os.walk(path_in, topdown=False):
        # 处理文件
        for filename in files:
            file_path = os.path.join(root, filename)
            if target in ["file", "all"] and keyword in filename and os.path.isfile(file_path):
                try:
                    os.remove(file_path)  # 删除文件
                    print(f"已删除文件: {file_path}")
                except Exception as e:
                    print(f"删除文件失败: {file_path}, 错误: {e}")

        # 处理目录
        for dirname in dirs:
            dir_path = os.path.join(root, dirname)
            if target in ["dir", "all"] and keyword in dirname and os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path)  # 删除目录及其内容
                    print(f"已删除目录: {dir_path}")
                except Exception as e:
                    print(f"删除目录失败: {dir_path}, 错误: {e}")