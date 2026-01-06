'''
图片压缩裁剪
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"E:\ws-code\test\test_in",
    "path_out": r"E:\ws-code\test\test_out",
    "keep_aspect_ratio" : True, # 保持长宽比缩放后裁剪
    "output_width" : 320,
    "output_height" : 240
}


img_cut(input_json)
