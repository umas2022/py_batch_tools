import os

def change_suffix(input_json: dict):
    """
    批量修改文件后缀名
    input_json 参数示例：
    {
        "path_in": "D:/ws-code/test/test_in",  # 输入文件夹
        "old_suffix": ".txt",                  # 要替换的旧后缀
        "new_suffix": ".md",                   # 新后缀
        "recursive": True                      # 是否遍历子目录
    }
    """
    path_in = input_json.get("path_in")
    old_suffix = input_json.get("old_suffix", "")
    new_suffix = input_json.get("new_suffix", "")
    recursive = input_json.get("recursive", False)

    if not os.path.exists(path_in):
        print(f"❌ 输入路径不存在: {path_in}")
        return

    count = 0
    # 如果 recursive=True，用 os.walk 遍历子目录，否则只处理一层
    walker = os.walk(path_in) if recursive else [(path_in, [], os.listdir(path_in))]

    for root, _, files in walker:
        for filename in files:
            old_path = os.path.join(root, filename)

            if not os.path.isfile(old_path):
                continue

            if filename.lower().endswith(old_suffix.lower()):
                name_without_suffix = filename[: -len(old_suffix)]
                new_filename = name_without_suffix + new_suffix
                new_path = os.path.join(root, new_filename)

                os.rename(old_path, new_path)
                count += 1
                print(f"✅ 重命名: {old_path} -> {new_path}")

    print(f"✨ 总共修改 {count} 个文件后缀")
