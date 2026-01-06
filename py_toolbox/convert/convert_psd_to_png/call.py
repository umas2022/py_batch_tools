'''
psd导出png
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    # 输入路径
    "path_in": r"E:\ws-code\test\test_in",
    # 输出路径
    "path_out": r"E:\ws-code\test\test_out",
    # 合并图层？
    "merge": False
}


psd_to_png(input_json)
