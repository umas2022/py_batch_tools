'''
删除输入目录下包含指定关键字的所有文件（遍历子目录）
'''

import sys, os

script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"D:\ws-code\test\test_in",
    "if_cut" : False,
    "cut_path" : r"D:\ws-code\test\test_out"
}


remove_duplicate_images(input_json)
