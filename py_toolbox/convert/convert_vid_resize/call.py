'''
视频分辨率压缩裁剪
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"E:\ws-code\test\test_in",
    "path_out": r"E:\ws-code\test\test_out",
    "keep_aspect_ratio" : True, # 保持长宽比缩放后裁剪
    "frame_rate" : 24,
    "output_width" : 480,
    "output_hight" : 480
}


video_resize(input_json)
