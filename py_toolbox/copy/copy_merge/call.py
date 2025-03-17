'''
拷贝合并
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"E:\ws-code\test\test_in",
    "path_out": r"E:\ws-code\test\test_out",
    # 是否计数
    "if_count": True,
    "flatten_level": 0  # 展平级数
}


copy_with_structure_flatten(input_json)
