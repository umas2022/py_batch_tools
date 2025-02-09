'''
多张图片合成gif
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"E:\ws-prj\串口屏T1-2.4寸\img_cut",
    "path_out": r"E:\ws-prj\串口屏T1-2.4寸\img_gif",
    "output_name": "output.gif",
    "frame_duration": 200,  # 每帧持续时间
    "loop": 0  # 无限循环
}


images_to_gif(input_json)
