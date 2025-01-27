'''
拷贝合并
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"path",
    "path_out": r"path",
    # 是否计数
    "if_count": True,
}


copy_with_structure_flatten(input_json)
