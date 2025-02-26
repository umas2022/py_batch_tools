import os
import subprocess

def video_cut(params):
    # 解析输入参数
    input_path = params.get('path_in')
    output_path = params.get('path_out')
    x_start = params.get('x_start')  # 归一化后的x轴起始位置或像素值
    x_end = params.get('x_end')      # 归一化后的x轴结束位置或像素值
    y_start = params.get('y_start')  # 归一化后的y轴起始位置或像素值
    y_end = params.get('y_end')      # 归一化后的y轴结束位置或像素值
    
    # 检查并创建输出目录
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # 遍历输入目录下的所有视频文件并进行裁剪
    for filename in os.listdir(input_path):
        if filename.endswith(('.mp4', '.avi', '.mov', '.flv', '.mkv')):  # 支持多种格式
            file_path = os.path.join(input_path, filename)
            output_file_path = os.path.join(output_path, filename)
            
            # 获取视频的宽度和高度
            command_probe = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "csv=p=0", file_path
            ]
            result = subprocess.run(command_probe, stdout=subprocess.PIPE, text=True)
            width, height = map(int, result.stdout.strip().split(','))
            
            # 判断输入是归一化比例还是像素值
            if x_start > 1 or x_end > 1 or y_start > 1 or y_end > 1:
                # 输入的是像素值，直接使用
                crop_x_start = int(x_start)
                crop_y_start = int(y_start)
                crop_width = int(x_end - x_start)
                crop_height = int(y_end - y_start)
            else:
                # 输入的是归一化比例，计算实际裁剪尺寸
                crop_width = int(width * (x_end - x_start))
                crop_height = int(height * (y_end - y_start))
                crop_x_start = int(width * x_start)
                crop_y_start = int(height * y_start)
            
            # 使用 ffmpeg 进行裁剪并保留音频
            command = [
                "ffmpeg", "-i", file_path, "-vf",
                f"crop={crop_width}:{crop_height}:{crop_x_start}:{crop_y_start}",
                "-c:a", "copy",  # 直接复制音频流，不重新编码
                "-y", output_file_path
            ]
            subprocess.run(command, check=True)
            print(f"已从视频 {filename} 中裁剪出 {output_file_path}")