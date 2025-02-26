import os
import subprocess

def video_compress(params):
    # 解析输入参数
    input_path = params.get('path_in')
    output_path = params.get('path_out')
    start_time = params.get('from')  # 开始时间（秒）
    end_time = params.get('to')  # 结束时间（秒）

    if not input_path or not output_path:
        print("错误：请输入有效的输入和输出路径。")
        return
    
    if start_time >= end_time or start_time < 0:
        print("错误：无效的时间范围。")
        return
    
    for filename in os.listdir(input_path):
        if filename.endswith(('.mp4', '.avi', '.mov', '.flv', '.mkv')):  # 支持的格式列表
            file_path = os.path.join(input_path, filename)
            output_file_path = os.path.join(output_path, filename)

            # 如果输出目录不存在，则创建
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            # 使用 ffmpeg 进行视频裁剪
            command = [
                "ffmpeg", "-i", file_path,
                "-ss", str(start_time), "-to", str(end_time),
                "-c", "copy", "-avoid_negative_ts", "make_zero",
                output_file_path, "-y"
            ]
            try:
                subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"成功处理文件 {filename}")
            except subprocess.CalledProcessError as e:
                print(f"处理文件 {filename} 失败: {e.stderr.decode()}")
