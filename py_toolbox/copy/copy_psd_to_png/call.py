'''
psd导出png
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"D:\wfs\麻生 2024.09.29.part1",
    "path_out": r"D:\wfs\麻生 2024.09.29.part1test",
    "merge": False # 暂不支持合并图层，有bug懒得修了 
}


psd_to_png(input_json)
