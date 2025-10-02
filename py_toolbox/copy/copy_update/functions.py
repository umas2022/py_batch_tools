import os
import sys
import time
from tqdm import tqdm

def count_files(path_in):
    """统计文件总数和大小，并显示扫描进度"""
    file_count = 0
    total_size = 0
    last_update = time.time()

    print("正在扫描文件以获取总数和大小，请稍候...")
    for root, dirs, files in os.walk(path_in):
        file_count += len(files)
        for f in files:
            try:
                total_size += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass

        # 每隔 1 秒输出一次扫描状态
        if time.time() - last_update > 1:
            print(f"已扫描 {file_count} 个文件，总大小 {total_size/1024/1024:.2f} MB ...")
            last_update = time.time()

    print(f"扫描完成：共 {file_count} 个文件，总大小 {total_size/1024/1024:.2f} MB")
    return file_count, total_size

def delete_extra_files(path_in, path_out):
    """删除备份目录中在源目录不存在的文件/目录"""
    for root, dirs, files in os.walk(path_out, topdown=False):
        rel_path = os.path.relpath(root, path_out)
        corresponding_in = os.path.join(path_in, rel_path)

        # 删除多余文件
        for f in files:
            out_file = os.path.join(root, f)
            in_file = os.path.join(corresponding_in, f)
            if not os.path.exists(in_file):
                print(f"删除多余文件: {out_file}")
                os.remove(out_file)

        # 删除多余目录
        for d in dirs:
            out_dir = os.path.join(root, d)
            in_dir = os.path.join(corresponding_in, d)
            if not os.path.exists(in_dir):
                print(f"删除多余目录: {out_dir}")
                os.rmdir(out_dir)


def copy_with_structure(input_json):
    path_in = input_json["path_in"]
    path_out = input_json["path_out"]

    delete_extra_files(path_in, path_out)

    # 先计数
    total_files, _ = count_files(path_in)

    # 用 tqdm 显示整体进度条
    with tqdm(total=total_files, desc="整体进度", unit="file") as pbar:
        for root, dirs, files in os.walk(path_in):
            rel_path = os.path.relpath(root, path_in)
            out_dir = os.path.join(path_out, rel_path)
            os.makedirs(out_dir, exist_ok=True)

            for f in files:
                src_file = os.path.join(root, f)
                dst_file = os.path.join(out_dir, f)
                try:
                    if not os.path.exists(dst_file) or os.path.getsize(src_file) != os.path.getsize(dst_file):
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        with open(src_file, "rb") as s, open(dst_file, "wb") as d:
                            d.write(s.read())
                except Exception as e:
                    print(f"复制失败: {src_file} -> {dst_file}, 错误: {e}")
                finally:
                    pbar.update(1)
