'''
获取gif中的所有帧，保存为png
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"E:\ws-code\test\test_in",
    "path_out": r"E:\ws-code\test\test_out",
}


extract_frames_from_gif(input_json)
