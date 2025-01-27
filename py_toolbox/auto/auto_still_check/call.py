'''
窗口静态检测
对比RGB三通道的ssim(结构相似度)，不计算hash，不能区分细微差异
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_cash": r"D:\ws-code\test\test_in",
    # "win_name": "Visual Studio Code",
    "win_name": "Bambu",
    "interval_time": 2
}


still_check(input_json)
