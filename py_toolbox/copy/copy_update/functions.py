'''
create: 2024.10.03
modify: 2026.01.06
备份更新，首先删除path_out中的旧内容，再以path_in目录为基准拷贝新内容到path_out
shutil.copy2()保留文件元数据（时间戳等），删除时比对文件大小和修改时间

多线程硬盘同步备份脚本
特点：
- 阶段化：清理 -> 构建任务 -> 并行复制
- 多线程复制（显著提速）
- 安全删除（不与复制并行）
- 实时进度反馈
'''

import os
import shutil
import filecmp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# ===================== 参数与默认配置 =====================

def check_inputs(cfg):
    cfg = dict(cfg)
    cfg.setdefault("if_count", True)
    cfg.setdefault("copy_workers", min(8, (os.cpu_count() or 4) * 2))
    cfg.setdefault("delete_workers", min(4, os.cpu_count() or 2))
    cfg.setdefault("report_interval", 2.0)
    return cfg


# ===================== 工具函数 =====================

def files_are_different(src, dst, time_tolerance=1):
    """
    高效文件一致性判断：
    - size 不同 → 不同
    - mtime 差异在容忍范围内 → 认为相同
    """
    try:
        src_stat = os.stat(src)
        dst_stat = os.stat(dst)

        if src_stat.st_size != dst_stat.st_size:
            return True

        if abs(src_stat.st_mtime - dst_stat.st_mtime) <= time_tolerance:
            return False

        return True  # mtime 不同，认为不同（不做内容比对）

    except OSError:
        return True

# ===================== 阶段 1：清理目标目录 =====================

def delete_worker(task):
    kind, path = task
    try:
        if kind == "file":
            os.remove(path)
        elif kind == "dir":
            shutil.rmtree(path)
        return True
    except Exception:
        return False


def clean_target(path_in, path_out, workers=4, report_interval=2.0):
    print("\n[STEP 1/3] Cleaning target directory...")
    start = last = time.time()

    delete_tasks = []
    scanned = 0

    for root, dirs, files in os.walk(path_out):
        rel = os.path.relpath(root, path_out)
        src_root = os.path.join(path_in, rel)

        # 整个目录不存在 → 删除
        if not os.path.exists(src_root):
            delete_tasks.append(("dir", root))
            continue

        for f in files:
            scanned += 1
            dst_file = os.path.join(root, f)
            src_file = os.path.join(src_root, f)

            if not os.path.exists(src_file) or files_are_different(src_file, dst_file):
                delete_tasks.append(("file", dst_file))

            now = time.time()
            if now - last > report_interval:
                print(f"  Scanned: {scanned} | Delete queued: {len(delete_tasks)}")
                last = now

    deleted = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(delete_worker, t) for t in delete_tasks]
        for f in as_completed(futures):
            if f.result():
                deleted += 1

    print(
        f"[DONE] Clean finished | Scanned: {scanned} | "
        f"Deleted: {deleted} | Time: {time.time() - start:.1f}s"
    )


# ===================== 阶段 2：构建复制任务 =====================

def count_files(path, report_interval=2.0):
    print("\n[STEP 2/3] Counting source files...")
    start = last = time.time()
    total = 0

    for _, _, files in os.walk(path):
        total += len(files)
        now = time.time()
        if now - last > report_interval:
            print(f"  Counted: {total}")
            last = now

    print(f"[DONE] Total files: {total} | Time: {time.time() - start:.1f}s")
    return total


def build_copy_tasks(path_in, path_out):
    tasks = []

    for root, _, files in os.walk(path_in):
        rel = os.path.relpath(root, path_in)
        dst_dir = os.path.join(path_out, rel)
        os.makedirs(dst_dir, exist_ok=True)

        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(dst_dir, f)
            tasks.append((src, dst))

    return tasks


# ===================== 阶段 3：并行复制 =====================

def copy_one(src, dst):
    try:
        if os.path.exists(dst):
            return "skipped"

        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, exist_ok=True)  # ⭐ 关键

        shutil.copy2(src, dst)
        return "copied"

    except FileNotFoundError:
        # 源文件或目标路径瞬间消失（并发下正常）
        return "failed"

    except Exception as e:
        return f"error: {e}"



def parallel_copy(tasks, workers=8, report_interval=2.0):
    print("\n[STEP 3/3] Parallel copying...")
    start = last = time.time()

    total = len(tasks)
    done = copied = skipped = failed = 0

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(copy_one, src, dst): (src, dst)
            for src, dst in tasks
        }

        for f in as_completed(futures):
            try:
                result = f.result()
            except Exception as e:
                result = f"error: {e}"

            done += 1
            if result == "copied":
                copied += 1
            elif result == "skipped":
                skipped += 1
            else:
                failed += 1

            now = time.time()
            if now - last > report_interval:
                speed = done / max(now - start, 0.1)
                percent = done / total * 100 if total else 100
                print(
                    f"  [{percent:5.1f}%] {done}/{total} | "
                    f"Copied: {copied} | Skipped: {skipped} | "
                    f"{speed:.1f} files/s"
                )
                last = now

    print(
        f"\n[DONE] Copy finished | Total: {total} | "
        f"Copied: {copied} | Skipped: {skipped} | "
        f"Time: {time.time() - start:.1f}s"
    )


# ===================== 主入口 =====================

def copy_with_structure(cfg):
    cfg = check_inputs(cfg)
    path_in = cfg["path_in"]
    path_out = cfg["path_out"]

    print("[INIT] Backup sync started")
    print(f"[INIT] Source: {path_in}")
    print(f"[INIT] Target: {path_out}")

    if not os.path.exists(path_in):
        print("[ERROR] Source path does not exist")
        return

    os.makedirs(path_out, exist_ok=True)

    try:
        clean_target(
            path_in,
            path_out,
            workers=cfg["delete_workers"],
            report_interval=cfg["report_interval"],
        )

        if cfg["if_count"]:
            total = count_files(path_in, cfg["report_interval"])
            if total == 0:
                print("[INFO] Nothing to copy")
                return

        print("\n[INFO] Building copy task list...")
        tasks = build_copy_tasks(path_in, path_out)
        print(f"[INFO] Tasks built: {len(tasks)}")

        parallel_copy(
            tasks,
            workers=cfg["copy_workers"],
            report_interval=cfg["report_interval"],
        )

    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Backup cancelled by user")


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        "path_in": r"C:\Users\umas_local\Documents\user",
        "path_out": r"D:\backup_dell_user",
        "if_count": True,
        "copy_workers": 8,     # HDD: 4~8, SSD: 8~16
        "delete_workers": 4,
        "report_interval": 2.0
    }

    copy_with_structure(config)
