'''
备份升级，删除差异
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
        "path_in": r"F:/",
        "path_out": r"H:/",
        "if_count": True,
        "copy_workers": 8,     # HDD: 4~8, SSD: 8~16
        "delete_workers": 4,
        "report_interval": 2.0
}


copy_with_structure(input_json)
