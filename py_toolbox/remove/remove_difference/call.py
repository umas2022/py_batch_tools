'''
以path_base目录为基准，删除path_del目录中多余的文件。
'''

import sys, os

script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_base": r"D:\ws-code\test\test_in",
    "path_del" : r"D:\ws-code\test\test_out",
    "target" : "all", # "file" or "dir" or "all"
}


remove_difference(input_json)
