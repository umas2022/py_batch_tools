'''
备份升级，删除差异
path_log可以在path_in内，但不能在path_out内
'''
from functions import *
import sys
import os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)


# # local -> ssd
# input_json = {
#     "path_in": r"C:\Users\umas_local\Documents\user\ws_diy",
#     "path_out": r"D:\ws_diy",
#     "path_log": r"D:\backup_log",
#     "if_count": True,
#     "copy_workers": 8,     # HDD: 4~8, SSD: 8~16
#     "delete_workers": 4,
#     "report_interval": 2.0
# }

# ssd -> local
input_json = {
    "path_in": r"D:\ws_diy",
    "path_out": r"C:\Users\umas_local\Documents\user\ws_diy",
    "path_log": r"D:\backup_log",
    "if_count": True,
    "copy_workers": 8,     # HDD: 4~8, SSD: 8~16
    "delete_workers": 4,
    "report_interval": 2.0
}


copy_with_structure(input_json)
