'''
文件名添加前缀
'''

import sys, os

script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"D:\ws-code\test\test_in",
    "prefix": "new_",
    "target": "dir",  # "file" or "dir" or "all"
}


add_prefix(input_json)
