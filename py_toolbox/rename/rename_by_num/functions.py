import os


def rename_files_by_sequence(input_json):
    # 从输入的 JSON 中获取必要的参数
    input_path = input_json.get("path_in")
    output_path = input_json.get("path_out")
    num_length = input_json.get("num_length", 4)
    overwrite = input_json.get("overwrite", False)

    # 检查输入路径是否存在
    if not os.path.exists(input_path):
        print(f"输入路径 {input_path} 不存在。")
        return

    # 如果不覆盖原文件且输出路径不存在，则创建输出路径
    if not overwrite and not os.path.exists(output_path):
        os.makedirs(output_path)

    # 获取输入路径下的所有文件
    file_list = os.listdir(input_path)
    # 按文件名排序
    file_list.sort()

    for index, filename in enumerate(file_list, start=1):
        file_path = os.path.join(input_path, filename)
        if os.path.isfile(file_path):
            # 获取文件扩展名
            file_extension = os.path.splitext(filename)[1]
            # 生成序号，根据 num_length 进行填充
            sequence_number = str(index).zfill(num_length)
            if overwrite:
                # 覆盖原文件，直接在原路径重命名
                new_filename = f"{sequence_number}{file_extension}"
                new_file_path = os.path.join(input_path, new_filename)
            else:
                # 不覆盖原文件，将文件复制到输出路径并重命名
                new_filename = f"{sequence_number}{file_extension}"
                new_file_path = os.path.join(output_path, new_filename)

            try:
                if overwrite:
                    # 直接重命名文件
                    os.rename(file_path, new_file_path)
                    print(f"已将 {file_path} 重命名为 {new_file_path}")
                else:
                    # 复制并重命名文件
                    with open(file_path, 'rb') as src_file, open(new_file_path, 'wb') as dst_file:
                        dst_file.write(src_file.read())
                    print(f"已将 {file_path} 复制并重命名为 {new_file_path}")
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
