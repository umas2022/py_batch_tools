'''
视频尺寸裁剪
输入坐标取0~1小数时，长宽归一化按比例裁剪
输入坐标为大于1整数时，按像素裁剪
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

# input_json = {
#     "path_in": r"E:\ws-code\test\test_in",
#     "path_out": r"E:\ws-code\test\test_out",
#     "x_start": 0.2,
#     "x_end" : 0.8,
#     "y_start" : 0,
#     "y_end" : 0.6
# }

input_json = {
    "path_in": r"E:\ws-code\test\test_in",
    "path_out": r"E:\ws-code\test\test_out",
    "x_start": 6,
    "x_end" : 726,
    "y_start" : 0,
    "y_end" : 720
}


video_cut(input_json)
