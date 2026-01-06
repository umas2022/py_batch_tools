import os
from mirage_white import build

def create_mirage_tank(input_json):
    # 解析输入参数
    path_in = os.path.normpath(input_json.get('path_in'))
    path_out = os.path.normpath(input_json.get('path_out'))

    # 检查输入路径是否存在
    if not os.path.exists(path_in):
        print(f"输入目录不存在: {path_in}")
        return

    # 遍历输入目录下的文件
    for root, dirs, files in os.walk(path_in):
        for file in files:
            full_in = os.path.join(root, file)
            relative_path = os.path.relpath(root, path_in)
            full_out_dir = os.path.join(path_out, relative_path)
            if not os.path.exists(full_out_dir):
                os.makedirs(full_out_dir)
            full_out = os.path.join(full_out_dir, file)
            full_out = full_out.split(".")
            full_out[-1] = "png"
            full_out = ".".join(full_out)

            try:
                build(full_in, full_out)
                print(f"成功为 {full_in} 创建幻影坦克图片")
            except Exception as e:
                print(f"为 {full_in} 创建幻影坦克图片时出错: {e}")


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        "path_in": r"D:\test\images",
        "path_out": r"D:\test\mirage",
    }
    create_mirage_tank(config)
