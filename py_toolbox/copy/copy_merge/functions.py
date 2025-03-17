import os
import shutil


def check_inputs(input_json):
    """赋值默认参数"""
    output_json = input_json
    if not 'if_count' in output_json:
        output_json['if_count'] = True
    if not 'flatten_level' in output_json:
        output_json['flatten_level'] = 0
    return output_json


def count_files(path_in):
    """计算输入目录下的所有文件数量"""
    file_count = 0
    for _, _, files in os.walk(path_in):
        file_count += len(files)
    return file_count
def copy_with_structure_flatten(input_json):
    input_json = check_inputs(input_json)
    path_in = input_json["path_in"]
    path_out = input_json["path_out"]
    flatten_level = input_json.get("flatten_level", 0)  # 默认为0级展平

    # 检查输入目录是否存在
    if not os.path.exists(path_in):
        print(f"Error: The source path {path_in} does not exist.")
        return

    total_files = count_files(path_in) if input_json['if_count'] else 0
    if total_files == 0:
        print(f"No files to copy in {path_in}.")
        return

    file_index = 0

    for root, dirs, files in os.walk(path_in):
        rel_path = os.path.relpath(root, path_in)
        split_rel_path = rel_path.split(os.sep)

        # 根据当前文件的相对路径深度和展平级别计算新的相对路径
        if len(split_rel_path) > flatten_level:
            keep_dirs = split_rel_path[:flatten_level]
            extra_path_parts = split_rel_path[flatten_level:]
        else:
            keep_dirs = split_rel_path
            extra_path_parts = []

        for file in files:
            file_index += 1
            src_file = os.path.join(root, file)

            if len(keep_dirs) > 0:
                # 当有需要保留的目录层级时
                kept_path = os.path.join(*keep_dirs)
                dest_file_name = f"{kept_path}{os.sep if kept_path else ''}{'.'.join(extra_path_parts)}.{file}" if extra_path_parts else os.path.join(kept_path, file)
            else:
                # 展平所有层级的情况
                dest_file_name = f"{'.'.join(extra_path_parts)}.{file}" if extra_path_parts else file

            dest_file = os.path.join(path_out, dest_file_name)

            if os.path.exists(dest_file):
                print(f"{file_index}/{total_files} Pass: {dest_file} already exists.")
            else:
                if not os.path.exists(os.path.dirname(dest_file)):
                    os.makedirs(os.path.dirname(dest_file))
                shutil.copy2(src_file, dest_file)
                print(f"{file_index}/{total_files} Copied: {src_file} to {dest_file}")

    print(f"All files copied from {path_in} to {path_out} while flattening the directory structure according to level {flatten_level}.")
