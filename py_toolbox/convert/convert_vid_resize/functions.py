import os
import subprocess

def video_resize(input_json):
    # 获取输入参数
    path_in = input_json["path_in"]
    path_out = input_json["path_out"]
    keep_aspect_ratio = input_json["keep_aspect_ratio"]
    frame_rate = input_json["frame_rate"]
    output_width = input_json["output_width"]
    output_height = input_json["output_hight"]

    # 确保输出目录存在
    if not os.path.exists(path_out):
        os.makedirs(path_out)

    # 遍历输入目录中的所有视频文件
    for filename in os.listdir(path_in):
        if filename.endswith((".mp4", ".avi", ".mov", ".mkv")):  # 可以根据需要添加更多格式
            input_file = os.path.join(path_in, filename)
            output_file = os.path.join(path_out, filename)

            # 构建ffmpeg命令
            if keep_aspect_ratio:
                # 保持长宽比，缩放后裁剪
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", input_file,
                    "-vf", f"fps={frame_rate},scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2",
                    "-c:v", "libx264",
                    "-crf", "23",  # 控制视频质量，值越小质量越高
                    "-preset", "medium",  # 编码速度与压缩率的平衡
                    output_file
                ]
            else:
                # 不保持长宽比，直接缩放
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", input_file,
                    "-vf", f"fps={frame_rate},scale={output_width}:{output_height}",
                    "-c:v", "libx264",
                    "-crf", "23",
                    "-preset", "medium",
                    output_file
                ]

            # 执行ffmpeg命令
            subprocess.run(ffmpeg_cmd)

    print("视频压缩裁剪完成！")


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        "path_in": r"D:\test\videos",
        "path_out": r"D:\test\output",
        "keep_aspect_ratio": True,
        "frame_rate": 30,
        "output_width": 1280,
        "output_hight": 720,
    }
    video_resize(config)