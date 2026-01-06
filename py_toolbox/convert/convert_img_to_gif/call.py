'''
多张图片合成gif
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"E:\ws-code\test\test_in",
    "path_out": r"E:\ws-code\test\test_out",
    "output_name": "output.gif",
    "frame_duration": 50,  # 每帧持续时间
    "loop": 0  # 无限循环
}


images_to_gif(input_json)
