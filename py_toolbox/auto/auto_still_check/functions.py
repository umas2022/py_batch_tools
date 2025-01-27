import os
import time
from shot_func import ShotFunc


def still_check(json_set):
    # 解析输入参数
    path_cash = os.path.normpath(str(json_set.get("path_cash", "")))
    win_name = str(json_set.get("win_name", ""))
    interval_time = int(json_set.get("interval_time", 1))

    # 相似度阈值
    grenze = 0.85
    # 重试检测时间,默认为3倍正常间隔
    recheck_time = 3 * interval_time

    sf = ShotFunc()
    s1_path = os.path.normpath(os.path.join(path_cash, "s1.jpg"))
    s2_path = os.path.normpath(os.path.join(path_cash, "s2.jpg"))

    # 删除可能存在的旧截图文件
    if os.path.isfile(s1_path):
        os.remove(s1_path)
    if os.path.isfile(s2_path):
        os.remove(s2_path)

    # 查找目标窗口句柄
    hwnd = sf.hwnd_match(win_name)
    if hwnd == "":
        print(f"未找到窗口: {win_name}")
        return

    def two_shot():
        """前后两次截图返回相似度,如果目录下已经存在s1.jpg和s2.jpg则保留s2并重命名为s1"""
        if os.path.isfile(s2_path):
            if os.path.isfile(s1_path):
                os.remove(s1_path)
            os.rename(s2_path, s1_path)
            sf.shot_window(hwnd, s2_path)
            time.sleep(interval_time)
        else:
            sf.shot_window(hwnd, s1_path)
            time.sleep(interval_time)
            sf.shot_window(hwnd, s2_path)
        try:
            return sf.compare_ssim(s1_path, s2_path)
        except Exception as e:
            print(f"SSIM比较出错: {e}")
            return 0

    def recheck():
        """检测到重复图片,延长等待时间并重新检测"""
        print("检测到静止状态，重新检查...")
        time.sleep(recheck_time)
        return two_shot()

    # 循环检测窗口是否静止
    while True:
        ssim_score = two_shot()
        print(f"相似度得分: {ssim_score:.2f}")
        if ssim_score > grenze:
            if recheck() > grenze:
                break

    print(f"{win_name} 已静止，可进行后续操作")
