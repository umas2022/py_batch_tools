'''
备份升级，删除差异
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"C:\Users\umas_local\Documents\user",
    "path_out": r"D:\backup_dell_user",
    # 是否计数
    "if_count": True,
}


copy_with_structure(input_json)
