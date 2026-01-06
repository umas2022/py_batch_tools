'''
图片生成幻影坦克
仅支持黑白图片
不能包含中文路径
'''
import sys, os
script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(script_path)
from functions import *

input_json = {
    "path_in": r"D:\ws-code\test\test_in",
    "path_out": r"D:\ws-code\test\test_out",
}


create_mirage_tank(input_json)
