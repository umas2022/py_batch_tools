'''
create: 2024.10.03
modify: 2026.02.07
备份更新。以path_in目录为基准，首先删除path_out中的旧内容，再拷贝新内容到path_out
shutil.copy2()保留文件元数据（时间戳等），删除时默认只比对文件大小和修改时间，compare_mode设为"content"时，进一步比对文件内容

'''

import os
import shutil
import time
import signal
import logging
import filecmp
import stat
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event


# ===================== 参数与默认配置 =====================

LOGGER = None


def to_fs_path(path):
    path = os.fspath(path)
    if os.name != "nt" or not path:
        return path
    if path.startswith("\\\\?\\") or path.startswith("\\\\.\\"):
        return path

    abs_path = os.path.abspath(path)
    if abs_path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + abs_path[2:]
    return "\\\\?\\" + abs_path


def from_fs_path(path):
    path = os.fspath(path)
    if os.name != "nt" or not path:
        return path
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[8:]
    if path.startswith("\\\\?\\"):
        return path[4:]
    return path


def fs_exists(path):
    return os.path.exists(to_fs_path(path))


def fs_isdir(path):
    return os.path.isdir(to_fs_path(path))


def fs_isfile(path):
    return os.path.isfile(to_fs_path(path))


def fs_islink(path):
    return os.path.islink(to_fs_path(path))


def fs_makedirs(path, exist_ok=True):
    os.makedirs(to_fs_path(path), exist_ok=exist_ok)


def fs_make_writable(path):
    fs_path = to_fs_path(path)
    os.chmod(fs_path, os.stat(fs_path).st_mode | stat.S_IWUSR)


def fs_remove(path):
    fs_path = to_fs_path(path)
    try:
        os.remove(fs_path)
    except PermissionError:
        fs_make_writable(fs_path)
        os.remove(fs_path)


def fs_rmtree(path):
    def remove_readonly(function, failed_path, exc_info):
        exception = exc_info if isinstance(exc_info, BaseException) else exc_info[1]
        if not isinstance(exception, PermissionError):
            raise exception
        fs_make_writable(failed_path)
        function(failed_path)

    kwargs = (
        {"onexc": remove_readonly}
        if sys.version_info >= (3, 12)
        else {"onerror": remove_readonly}
    )
    shutil.rmtree(to_fs_path(path), **kwargs)


def fs_stat(path):
    return os.stat(to_fs_path(path))


def fs_copy2(src, dst):
    shutil.copy2(to_fs_path(src), to_fs_path(dst))


def fs_replace(src, dst):
    os.replace(to_fs_path(src), to_fs_path(dst))


def fs_walk(path):
    return os.walk(to_fs_path(path))


def setup_logger(path_log):
    global LOGGER
    LOGGER = logging.getLogger("backup_sync")
    LOGGER.setLevel(logging.INFO)
    for handler in LOGGER.handlers:
        handler.close()
    LOGGER.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    LOGGER.addHandler(ch)

    if path_log:
        fs_makedirs(path_log, exist_ok=True)
        log_file = os.path.join(
            path_log, f"backup_sync_{time.strftime('%Y%m%d_%H%M%S')}.log"
        )
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        LOGGER.addHandler(fh)

    return LOGGER


def close_logger():
    global LOGGER
    if not LOGGER:
        return
    for handler in LOGGER.handlers:
        handler.flush()
        handler.close()
    LOGGER.handlers.clear()
    LOGGER = None


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
    for root, dirs, files in fs_walk(path_log):
        root = from_fs_path(root)
        if cancel_event.is_set():
            return
        rel_root = os.path.relpath(root, path_log)
        dst_root = os.path.join(dst_log, rel_root)
        fs_makedirs(dst_root, exist_ok=True)
        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(dst_root, f)
            try:
                fs_copy2(src, dst)
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
    cfg.setdefault("dry_run", False)
    cfg.setdefault("allow_empty_source", False)
    return cfg


# ===================== 工具函数 =====================

def files_are_different(src, dst, time_tolerance=1, compare_mode="mtime"):
    """
    高效文件一致性判断：
    - size 不同 → 不同
    - mtime 差异在容忍范围内 → 认为相同
    """
    try:
        src_stat = fs_stat(src)
        dst_stat = fs_stat(dst)

        if src_stat.st_size != dst_stat.st_size:
            return True

        if abs(src_stat.st_mtime - dst_stat.st_mtime) <= time_tolerance:
            return False

        if compare_mode == "content":
            return not filecmp.cmp(to_fs_path(src), to_fs_path(dst), shallow=False)

        return True  # mtime 不同，认为不同（不做内容比对）

    except OSError:
        return True

# ===================== 阶段 1：清理目标目录 =====================

def delete_worker(task, cancel_event):
    kind, path = task
    if cancel_event.is_set():
        return False, kind, path, "cancelled"
    try:
        if kind == "file":
            fs_remove(path)
        elif kind == "dir":
            fs_rmtree(path)
        else:
            raise ValueError(f"Unknown delete task kind: {kind}")
        if fs_exists(path):
            raise OSError("path still exists after deletion")
        return True, kind, path, None
    except Exception as e:
        return False, kind, path, str(e)


def clean_target(
    path_in,
    path_out,
    workers=4,
    report_interval=2.0,
    time_tolerance=1,
    compare_mode="mtime",
    cancel_event=None,
    dry_run=False,
):
    log("\n[STEP 1/3] Cleaning target directory...")
    start = last = time.time()
    cancel_event = cancel_event or Event()

    delete_tasks = []
    scanned = 0

    for root, dirs, files in fs_walk(path_out):
        root = from_fs_path(root)
        if cancel_event.is_set():
            log("[INTERRUPTED] Cancelled during scanning")
            return
        rel = os.path.relpath(root, path_out)
        src_root = os.path.join(path_in, rel)

        # 源端不存在此目录，或源端同名路径其实是文件 → 删除整个目标目录
        if not fs_isdir(src_root):
            delete_tasks.append(("dir", root))
            dirs[:] = []
            continue

        for f in files:
            scanned += 1
            dst_file = os.path.join(root, f)
            src_file = os.path.join(src_root, f)

            # 有源文件时交给复制阶段原子覆盖，避免先删后复制造成备份缺口。
            if not fs_isfile(src_file):
                delete_tasks.append(("file", dst_file))

            now = time.time()
            if now - last > report_interval:
                log(f"  Scanned: {scanned} | Delete queued: {len(delete_tasks)}")
                last = now

    if dry_run:
        for kind, path in delete_tasks:
            log(f"[DRY RUN] Would delete {kind}: {path}")
        log(
            f"[DRY RUN] Clean preview finished | Scanned: {scanned} | "
            f"Would delete: {len(delete_tasks)} | "
            f"Time: {time.time() - start:.1f}s"
        )
        return {
            "queued": len(delete_tasks),
            "deleted": 0,
            "failed": 0,
            "failures": [],
            "dry_run": True,
        }

    deleted = 0
    failures = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(delete_worker, t, cancel_event) for t in delete_tasks]
        for f in as_completed(futures):
            if cancel_event.is_set():
                break
            success, kind, path, error = f.result()
            if success:
                deleted += 1
            else:
                failures.append((kind, path, error))
                log(
                    f"[ERROR] Failed to delete {kind}: {path} | {error}",
                    level="error",
                )

    log(
        f"[DONE] Clean finished | Scanned: {scanned} | "
        f"Deleted: {deleted} | Failed: {len(failures)} | "
        f"Time: {time.time() - start:.1f}s"
    )
    return {
        "queued": len(delete_tasks),
        "deleted": deleted,
        "failed": len(failures),
        "failures": failures,
        "dry_run": False,
    }


# ===================== 阶段 2：构建复制任务 =====================

def count_files(path, report_interval=2.0, cancel_event=None, exclude_dir=None):
    log("\n[STEP 2/3] Counting source files...")
    start = last = time.time()
    total = 0
    cancel_event = cancel_event or Event()
    exclude_dir = os.path.realpath(exclude_dir) if exclude_dir else None

    for root, dirs, files in fs_walk(path):
        root = from_fs_path(root)
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
        total += sum(
            1
            for name in files
            if not (
                fs_islink(os.path.join(root, name))
                and not fs_exists(os.path.join(root, name))
            )
        )
        now = time.time()
        if now - last > report_interval:
            log(f"  Counted: {total}")
            last = now

    log(f"[DONE] Total files: {total} | Time: {time.time() - start:.1f}s")
    return total


def iter_copy_tasks(path_in, path_out, cancel_event=None, exclude_dir=None):
    cancel_event = cancel_event or Event()
    exclude_dir = os.path.realpath(exclude_dir) if exclude_dir else None
    for root, dirs, files in fs_walk(path_in):
        root = from_fs_path(root)
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
        if not files and not dirs:
            try:
                fs_makedirs(dst_dir, exist_ok=True)
            except OSError as e:
                log(
                    f"error: Cannot create empty directory: {e} | dst={dst_dir}",
                    level="error",
                )

        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(dst_dir, f)
            if fs_islink(src) and not fs_exists(src):
                log(f"[SKIPPED] Broken symbolic link: {src}")
                continue
            yield (src, dst)


def build_copy_tasks(path_in, path_out, cancel_event=None, exclude_dir=None):
    return list(
        iter_copy_tasks(
            path_in, path_out, cancel_event=cancel_event, exclude_dir=exclude_dir
        )
    )


# ===================== 阶段 3：并行复制 =====================

def copy_one(
    src,
    dst,
    cancel_event,
    time_tolerance=1,
    compare_mode="mtime",
):
    try:
        if cancel_event.is_set():
            return "cancelled"
        if fs_exists(dst):
            if not fs_isfile(dst):
                return f"error: Target is not a file | src={src} | dst={dst}"
            if not files_are_different(
                src,
                dst,
                time_tolerance=time_tolerance,
                compare_mode=compare_mode,
            ):
                return "skipped"

        dst_dir = os.path.dirname(dst)
        fs_makedirs(dst_dir, exist_ok=True)
        temp_dst = os.path.join(
            dst_dir,
            f".{os.path.basename(dst)}.{uuid.uuid4().hex}.backup_tmp",
        )
        try:
            fs_copy2(src, temp_dst)
            if fs_exists(dst):
                fs_make_writable(dst)
            fs_replace(temp_dst, dst)
        finally:
            if fs_exists(temp_dst):
                fs_remove(temp_dst)
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
    time_tolerance=1,
    compare_mode="mtime",
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
            futures.add(
                ex.submit(
                    copy_one,
                    src,
                    dst,
                    cancel_event,
                    time_tolerance,
                    compare_mode,
                )
            )
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
    return {
        "copied": copied,
        "skipped": skipped,
        "failed": failed,
        "total": total,
    }


# ===================== 主入口 =====================

def copy_with_structure(cfg):
    cfg = check_inputs(cfg)
    path_in = cfg["path_in"]
    path_out = cfg["path_out"]
    path_log = cfg["path_log"]

    src_real = os.path.abspath(os.path.realpath(path_in))
    dst_real = os.path.abspath(os.path.realpath(path_out))

    if src_real == dst_real or is_subpath(src_real, dst_real) or is_subpath(dst_real, src_real):
        print("[ERROR] Source and target paths overlap. Abort to avoid data loss.")
        return False

    if path_log:
        log_real = os.path.realpath(path_log)
        if is_subpath(dst_real, log_real):
            print("[ERROR] path_log is inside path_out. This is not allowed.")
            return False

    # 预演不创建日志目录，保证 dry_run 对文件系统完全只读。
    setup_logger(None if cfg["dry_run"] else path_log)

    log("[INIT] Backup sync started")
    log(f"[INIT] Source: {path_in}")
    log(f"[INIT] To: {path_out}")
    if cfg["dry_run"]:
        log("[INIT] DRY RUN: no files or directories will be changed")

    if not fs_isdir(path_in):
        log("[ERROR] Source directory does not exist", level="error")
        close_logger()
        return False

    if not fs_exists(path_out):
        if cfg["dry_run"]:
            log("[DRY RUN] Target directory does not exist; it would be created")
        else:
            fs_makedirs(path_out, exist_ok=True)
    elif not fs_isdir(path_out):
        log("[ERROR] Target path exists but is not a directory", level="error")
        close_logger()
        return False

    with os.scandir(to_fs_path(path_in)) as entries:
        source_is_empty = next(entries, None) is None
    target_has_entries = False
    if fs_isdir(path_out):
        with os.scandir(to_fs_path(path_out)) as entries:
            target_has_entries = next(entries, None) is not None
    if source_is_empty and target_has_entries and not cfg["allow_empty_source"]:
        log(
            "[ERROR] Source is empty while target is not. "
            "Abort to avoid deleting the whole backup. "
            "Set allow_empty_source=True only when this is intentional.",
            level="error",
        )
        close_logger()
        return False

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
        clean_result = clean_target(
            path_in,
            path_out,
            workers=cfg["delete_workers"],
            report_interval=cfg["report_interval"],
            time_tolerance=cfg["time_tolerance"],
            compare_mode=cfg["compare_mode"],
            cancel_event=cancel_event,
            dry_run=cfg["dry_run"],
        )

        if cancel_event.is_set():
            return False

        cleanup_incomplete = clean_result["failed"] > 0
        if cleanup_incomplete:
            log(
                "[WARNING] Target cleanup was incomplete. "
                "Copying will continue so source files are still backed up.",
                level="warning",
            )

        if cfg["dry_run"]:
            total = count_files(
                path_in,
                cfg["report_interval"],
                cancel_event=cancel_event,
                exclude_dir=exclude_dir,
            )
            log(
                f"[DRY RUN] Preview complete | Source files: {total} | "
                f"Would delete: {clean_result['queued']}"
            )
            return True

        total = None
        if cfg["if_count"]:
            total = count_files(
                path_in,
                cfg["report_interval"],
                cancel_event=cancel_event,
                exclude_dir=exclude_dir,
            )
            if total == 0:
                log("[INFO] Source contains no files; directory structure will still be synced")
            if cancel_event.is_set():
                return False

        copy_result = parallel_copy_stream(
            path_in,
            path_out,
            workers=cfg["copy_workers"],
            report_interval=cfg["report_interval"],
            cancel_event=cancel_event,
            total=total,
            max_in_flight=cfg["max_in_flight"],
            exclude_dir=exclude_dir,
            time_tolerance=cfg["time_tolerance"],
            compare_mode=cfg["compare_mode"],
        )

        if log_in_source and not cancel_event.is_set():
            sync_log_dir(path_log, path_in, path_out, cancel_event=cancel_event)
        if cleanup_incomplete:
            log(
                "[INCOMPLETE] Source copy was attempted, but some stale target "
                "items could not be removed. Review the deletion errors above.",
                level="error",
            )
        return copy_result["failed"] == 0 and not cleanup_incomplete

    except KeyboardInterrupt:
        log("\n[INTERRUPTED] Backup cancelled by user")
        return False
    finally:
        signal.signal(signal.SIGINT, old_handler)
        close_logger()


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
