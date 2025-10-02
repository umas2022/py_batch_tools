'''
批量修改后缀名
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"D:\ws-code\test\test_in",
    "old_suffix": ".txt",
    "new_suffix": ".md",
}


change_suffix(input_json)
