import cv2
import os

def extract_frames_from_videos(input_json):
    # 从输入的 JSON 中获取必要的参数
    input_dir = input_json.get("path_in")
    output_dir = input_json.get("path_out")
    frame_rate = input_json.get("frame_rate")

    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"输入目录 {input_dir} 不存在。")
        return
    
    # 若输出目录不存在，则创建它
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍历输入目录下的所有文件
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        
        # 检查文件是否为视频文件，现在包括 .mkv 格式
        if os.path.isfile(file_path) and filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            try:
                # 创建以视频名（不含后缀）命名的子文件夹
                video_name_without_ext = os.path.splitext(filename)[0]
                video_folder_path = os.path.join(output_dir, video_name_without_ext)
                
                if not os.path.exists(video_folder_path):
                    os.makedirs(video_folder_path)

                # 打开视频文件
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    print(f"无法打开视频文件: {file_path}")
                    continue

                # 获取视频的原始帧率
                original_frame_rate = cap.get(cv2.CAP_PROP_FPS)
                # 计算帧间隔
                frame_interval = int(original_frame_rate / frame_rate)

                frame_count = 0
                output_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    # 按指定帧率提取帧
                    if frame_count % frame_interval == 0:
                        # 构建输出图片的文件名
                        output_filename = f"frame_{output_count:04d}.jpg"
                        output_file_path = os.path.join(video_folder_path, output_filename)
                        # 保存帧为图片
                        cv2.imwrite(output_file_path, frame)
                        if os.path.exists(output_file_path):
                            print(f"Frame {output_count} saved successfully.")
                        else:
                            print(f"Failed to save frame {output_count}.")
                        output_count += 1
                    frame_count += 1

                # 释放视频捕获对象
                cap.release()
                print(f"已从视频 {filename} 中提取 {output_count} 帧图片，保存到 {video_folder_path}。")
            except Exception as e:
                print(f"处理视频 {file_path} 时出错: {e}")


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        "path_in": r"D:\test\videos",
        "path_out": r"D:\test\frames",
        "frame_rate": 1,
    }
    extract_frames_from_videos(config)

