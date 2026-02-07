'''
create: 2024.10.03
modify: 2026.02.07
备份更新，首先删除path_out中的旧内容，再以path_in目录为基准拷贝新内容到path_out
shutil.copy2()保留文件元数据（时间戳等），删除时默认只比对文件大小和修改时间，compare_mode设为"content"时，进一步比对文件内容

'''

import os
import shutil
import time
import signal
import logging
import filecmp
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event


# ===================== 参数与默认配置 =====================

LOGGER = None
ERROR_LOG_PATH = None


def setup_logger(path_log):
    global LOGGER, ERROR_LOG_PATH
    LOGGER = logging.getLogger("backup_sync")
    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    LOGGER.addHandler(ch)

    if path_log:
        os.makedirs(path_log, exist_ok=True)
        log_file = os.path.join(
            path_log, f"backup_sync_{time.strftime('%Y%m%d_%H%M%S')}.log"
        )
        ERROR_LOG_PATH = os.path.join(path_log, "errors.log")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        LOGGER.addHandler(fh)

        eh = logging.FileHandler(ERROR_LOG_PATH, encoding="utf-8")
        eh.setLevel(logging.ERROR)
        eh.setFormatter(fmt)
        LOGGER.addHandler(eh)

    return LOGGER


def log(msg, level="info"):
    if LOGGER:
        getattr(LOGGER, level)(msg)
    else:
        print(msg)


def is_subpath(parent, child):
    if not parent or not child:
        return False
    parent = os.path.abspath(os.path.realpath(parent))
    child = os.path.abspath(os.path.realpath(child))
    try:
        return os.path.commonpath([parent, child]) == parent
    except ValueError:
        # 不同盘符或路径类型不一致时，认为不是子路径
        return False


def sync_log_dir(path_log, path_in, path_out, cancel_event=None):
    cancel_event = cancel_event or Event()
    if not path_log:
        return
    if cancel_event.is_set():
        return
    rel = os.path.relpath(path_log, path_in)
    dst_log = os.path.join(path_out, rel)
    log(f"[INFO] Syncing log directory to target: {dst_log}")
    for root, dirs, files in os.walk(path_log):
        if cancel_event.is_set():
            return
        rel_root = os.path.relpath(root, path_log)
        dst_root = os.path.join(dst_log, rel_root)
        os.makedirs(dst_root, exist_ok=True)
        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(dst_root, f)
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                log(f"error: {e} | src={src} | dst={dst}", level="error")


def check_inputs(cfg):
    cfg = dict(cfg)
    cfg.setdefault("if_count", True)
    cfg.setdefault("copy_workers", min(8, (os.cpu_count() or 4) * 2))
    cfg.setdefault("delete_workers", min(4, os.cpu_count() or 2))
    cfg.setdefault("report_interval", 2.0)
    cfg.setdefault("time_tolerance", 1)
    cfg.setdefault("compare_mode", "mtime")  # mtime | content
    cfg.setdefault("path_log", None)
    cfg.setdefault("max_in_flight", None)
    return cfg


# ===================== 工具函数 =====================

def files_are_different(src, dst, time_tolerance=1, compare_mode="mtime"):
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

        if compare_mode == "content":
            return not filecmp.cmp(src, dst, shallow=False)

        return True  # mtime 不同，认为不同（不做内容比对）

    except OSError:
        return True

# ===================== 阶段 1：清理目标目录 =====================

def delete_worker(task, cancel_event):
    kind, path = task
    if cancel_event.is_set():
        return False
    try:
        if kind == "file":
            os.remove(path)
        elif kind == "dir":
            shutil.rmtree(path)
        return True
    except Exception:
        return False


def clean_target(
    path_in,
    path_out,
    workers=4,
    report_interval=2.0,
    time_tolerance=1,
    compare_mode="mtime",
    cancel_event=None,
):
    log("\n[STEP 1/3] Cleaning target directory...")
    start = last = time.time()
    cancel_event = cancel_event or Event()

    delete_tasks = []
    scanned = 0

    for root, dirs, files in os.walk(path_out):
        if cancel_event.is_set():
            log("[INTERRUPTED] Cancelled during scanning")
            return
        rel = os.path.relpath(root, path_out)
        src_root = os.path.join(path_in, rel)

        # 整个目录不存在 → 删除
        if not os.path.exists(src_root):
            delete_tasks.append(("dir", root))
            dirs[:] = []
            continue

        for f in files:
            scanned += 1
            dst_file = os.path.join(root, f)
            src_file = os.path.join(src_root, f)

            if not os.path.exists(src_file) or files_are_different(
                src_file,
                dst_file,
                time_tolerance=time_tolerance,
                compare_mode=compare_mode,
            ):
                delete_tasks.append(("file", dst_file))

            now = time.time()
            if now - last > report_interval:
                log(f"  Scanned: {scanned} | Delete queued: {len(delete_tasks)}")
                last = now

    deleted = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(delete_worker, t, cancel_event) for t in delete_tasks]
        for f in as_completed(futures):
            if cancel_event.is_set():
                break
            if f.result():
                deleted += 1

    log(
        f"[DONE] Clean finished | Scanned: {scanned} | "
        f"Deleted: {deleted} | Time: {time.time() - start:.1f}s"
    )


# ===================== 阶段 2：构建复制任务 =====================

def count_files(path, report_interval=2.0, cancel_event=None, exclude_dir=None):
    log("\n[STEP 2/3] Counting source files...")
    start = last = time.time()
    total = 0
    cancel_event = cancel_event or Event()
    exclude_dir = os.path.realpath(exclude_dir) if exclude_dir else None

    for root, dirs, files in os.walk(path):
        if cancel_event.is_set():
            log("[INTERRUPTED] Cancelled during counting")
            return total
        if exclude_dir and is_subpath(exclude_dir, root):
            dirs[:] = []
            continue
        if exclude_dir:
            dirs[:] = [
                d for d in dirs if not is_subpath(exclude_dir, os.path.join(root, d))
            ]
        total += len(files)
        now = time.time()
        if now - last > report_interval:
            log(f"  Counted: {total}")
            last = now

    log(f"[DONE] Total files: {total} | Time: {time.time() - start:.1f}s")
    return total


def iter_copy_tasks(path_in, path_out, cancel_event=None, exclude_dir=None):
    cancel_event = cancel_event or Event()
    exclude_dir = os.path.realpath(exclude_dir) if exclude_dir else None
    for root, dirs, files in os.walk(path_in):
        if cancel_event.is_set():
            log("[INTERRUPTED] Cancelled during task build")
            return
        if exclude_dir and is_subpath(exclude_dir, root):
            dirs[:] = []
            continue
        if exclude_dir:
            dirs[:] = [
                d for d in dirs if not is_subpath(exclude_dir, os.path.join(root, d))
            ]
        rel = os.path.relpath(root, path_in)
        dst_dir = os.path.join(path_out, rel)
        os.makedirs(dst_dir, exist_ok=True)

        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(dst_dir, f)
            yield (src, dst)


def build_copy_tasks(path_in, path_out, cancel_event=None, exclude_dir=None):
    return list(
        iter_copy_tasks(
            path_in, path_out, cancel_event=cancel_event, exclude_dir=exclude_dir
        )
    )


# ===================== 阶段 3：并行复制 =====================

def copy_one(src, dst, cancel_event):
    try:
        if cancel_event.is_set():
            return "cancelled"
        if os.path.exists(dst):
            return "skipped"

        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, exist_ok=True)  # ⭐ 关键

        shutil.copy2(src, dst)
        return "copied"

    except FileNotFoundError:
        # 源文件或目标路径瞬间消失（并发下正常）
        return f"error: FileNotFound | src={src} | dst={dst}"

    except Exception as e:
        return f"error: {e} | src={src} | dst={dst}"



def parallel_copy_stream(
    path_in,
    path_out,
    workers=8,
    report_interval=2.0,
    cancel_event=None,
    total=None,
    max_in_flight=None,
    exclude_dir=None,
):
    log("\n[STEP 3/3] Parallel copying...")
    start = last = time.time()
    cancel_event = cancel_event or Event()
    max_in_flight = max_in_flight or max(8, workers * 4)

    done = copied = skipped = failed = 0
    def handle_result(f):
        nonlocal done, copied, skipped, failed, last
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
            if isinstance(result, str) and result.startswith("error:"):
                log(result, level="error")

        now = time.time()
        if now - last > report_interval:
            speed = done / max(now - start, 0.1)
            if total:
                percent = done / total * 100
                log(
                    f"  [{percent:5.1f}%] {done}/{total} | "
                    f"Copied: {copied} | Skipped: {skipped} | "
                    f"{speed:.1f} files/s"
                )
            else:
                log(
                    f"  {done} done | Copied: {copied} | "
                    f"Skipped: {skipped} | {speed:.1f} files/s"
                )
            last = now

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = set()
        for src, dst in iter_copy_tasks(
            path_in, path_out, cancel_event=cancel_event, exclude_dir=exclude_dir
        ):
            if cancel_event.is_set():
                break
            futures.add(ex.submit(copy_one, src, dst, cancel_event))
            if len(futures) >= max_in_flight:
                done_f = next(as_completed(futures))
                futures.remove(done_f)
                handle_result(done_f)

        for f in as_completed(futures):
            if cancel_event.is_set():
                break
            handle_result(f)

    total_text = f"{total}" if total is not None else "unknown"
    log(
        f"\n[DONE] Copy finished | Total: {total_text} | "
        f"Copied: {copied} | Skipped: {skipped} | "
        f"Failed: {failed} | Time: {time.time() - start:.1f}s"
    )


# ===================== 主入口 =====================

def copy_with_structure(cfg):
    cfg = check_inputs(cfg)
    path_in = cfg["path_in"]
    path_out = cfg["path_out"]
    path_log = cfg["path_log"]

    if path_log:
        log_real = os.path.realpath(path_log)
        dst_real = os.path.realpath(path_out)
        if is_subpath(dst_real, log_real):
            print("[ERROR] path_log is inside path_out. This is not allowed.")
            return

    setup_logger(path_log)

    log("[INIT] Backup sync started")
    log(f"[INIT] Source: {path_in}")
    log(f"[INIT] Target: {path_out}")

    if not os.path.exists(path_in):
        log("[ERROR] Source path does not exist", level="error")
        return

    os.makedirs(path_out, exist_ok=True)

    src_real = os.path.realpath(path_in)
    dst_real = os.path.realpath(path_out)
    if is_subpath(src_real, dst_real):
        log("[ERROR] Target path is inside source path. Abort to avoid recursion.", level="error")
        return

    log_real = os.path.realpath(path_log) if path_log else None
    log_in_source = bool(log_real and is_subpath(src_real, log_real))
    exclude_dir = log_real if log_in_source else None

    cancel_event = Event()

    def _on_sigint(signum, frame):
        if not cancel_event.is_set():
            cancel_event.set()
            log("\n[INTERRUPTED] Cancelling... (waiting for threads to finish)")

    old_handler = signal.signal(signal.SIGINT, _on_sigint)

    try:
        clean_target(
            path_in,
            path_out,
            workers=cfg["delete_workers"],
            report_interval=cfg["report_interval"],
            time_tolerance=cfg["time_tolerance"],
            compare_mode=cfg["compare_mode"],
            cancel_event=cancel_event,
        )

        if cancel_event.is_set():
            return

        total = None
        if cfg["if_count"]:
            total = count_files(
                path_in,
                cfg["report_interval"],
                cancel_event=cancel_event,
                exclude_dir=exclude_dir,
            )
            if total == 0:
                log("[INFO] Nothing to copy")
                return
            if cancel_event.is_set():
                return

        parallel_copy_stream(
            path_in,
            path_out,
            workers=cfg["copy_workers"],
            report_interval=cfg["report_interval"],
            cancel_event=cancel_event,
            total=total,
            max_in_flight=cfg["max_in_flight"],
            exclude_dir=exclude_dir,
        )

        if log_in_source and not cancel_event.is_set():
            sync_log_dir(path_log, path_in, path_out, cancel_event=cancel_event)

    except KeyboardInterrupt:
        log("\n[INTERRUPTED] Backup cancelled by user")
    finally:
        signal.signal(signal.SIGINT, old_handler)


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        # "path_in": r"D:\ws-code\test\test_in",
        # "path_out": r"D:\ws-code\test\test_out",
        # "path_log": r"D:\ws-code\test\test_log",
        # "if_count": True,
        # "copy_workers": 8,     # HDD: 4~8, SSD: 8~16
        # "delete_workers": 4,
        # "report_interval": 2.0
        "path_in": r"F:/",
        "path_out": r"Z:/",
        "path_log": r"F:/backup_log",
        "if_count": True,
        "copy_workers": 8,     # HDD: 4~8, SSD: 8~16
        "delete_workers": 4,
        "report_interval": 2.0
    }

    copy_with_structure(config)
