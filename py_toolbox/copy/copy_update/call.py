'''
备份升级，删除差异
path_log可以在path_in内，但不能在path_out内
'''
from functions import *
import sys
import os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)


# # dell_diy local -> ssd
# input_json = {
#     "path_in": r"C:\Users\umas_local\Documents\user\ws_diy",
#     "path_out": r"D:\backup_dell_user\ws_diy",
#     "path_log": r"D:\backup_log",
#     "if_count": True,
#     "copy_workers": 8,     # HDD: 4~8, SSD: 8~16
#     "delete_workers": 4,
#     "report_interval": 2.0
# }

# # dell_diy ssd -> local
# input_json = {
#     "path_in": r"D:\backup_dell_user\ws_diy",
#     "path_out": r"C:\Users\umas_local\Documents\user\ws_diy",
#     "path_log": r"D:\backup_log",
#     "if_count": True,
#     "copy_workers": 8,     # HDD: 4~8, SSD: 8~16
#     "delete_workers": 4,
#     "report_interval": 2.0
# }

# dell_user local -> ssd
input_json = {
    "path_in": r"C:\Users\umas_local\Documents\user",
    "path_out": r"D:\backup_dell_user",
    "path_log": r"D:\backup_log",
    "if_count": True,
    "copy_workers": 16,     # HDD: 4~8, SSD: 8~16
    "delete_workers": 4,
    "report_interval": 2.0,
    # 先预演并检查控制台输出；确认待删除列表无误后再改为 False。
    "dry_run": False
}


copy_with_structure(input_json)
