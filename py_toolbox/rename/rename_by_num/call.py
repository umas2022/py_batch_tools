'''
按数字命名
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"E:\ws-code\test\test_in",
    "path_out": r"E:\ws-code\test\test_out",
    "num_length" : 4,
    "overwrite" : False # 启用overwrite时path_out不生效
}


rename_files_by_sequence(input_json)
