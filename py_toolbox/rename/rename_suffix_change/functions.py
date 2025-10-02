import os

def change_suffix(input_json: dict):
    """
    批量修改文件后缀名
    input_json 参数示例：
    {
        "path_in": "D:/ws-code/test/test_in",  # 输入文件夹
        "old_suffix": ".txt",                  # 要替换的旧后缀
        "new_suffix": ".md",                   # 新后缀
    }
    """
    path_in = input_json.get("path_in")
    old_suffix = input_json.get("old_suffix", "")
    new_suffix = input_json.get("new_suffix", "")

    if not os.path.exists(path_in):
        print(f"❌ 输入路径不存在: {path_in}")
        return

    count = 0
    for filename in os.listdir(path_in):
        old_path = os.path.join(path_in, filename)

        # 跳过目录
        if not os.path.isfile(old_path):
            continue

        # 判断后缀是否匹配
        if filename.lower().endswith(old_suffix.lower()):
            name_without_suffix = filename[: -len(old_suffix)]
            new_filename = name_without_suffix + new_suffix
            new_path = os.path.join(path_in, new_filename)

            os.rename(old_path, new_path)
            count += 1
            print(f"✅ 重命名: {filename} -> {new_filename}")

    print(f"✨ 总共修改 {count} 个文件后缀")
