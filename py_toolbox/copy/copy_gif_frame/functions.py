from PIL import Image
import os

def extract_frames_from_gif(input_json):
    # 从输入的 JSON 中获取必要的参数
    path_in = input_json.get("path_in")
    path_out = input_json.get("path_out")

    # 检查输入路径和输出路径是否存在
    if not os.path.exists(path_in):
        print(f"输入路径 {path_in} 不存在，请检查。")
        return
    if not os.path.exists(path_out):
        os.makedirs(path_out)

    # 遍历输入路径下的所有文件
    for filename in os.listdir(path_in):
        file_path = os.path.join(path_in, filename)
        # 检查文件是否为 GIF 文件
        if os.path.isfile(file_path) and filename.lower().endswith('.gif'):
            try:
                # 打开 GIF 文件
                with Image.open(file_path) as img:
                    gif_name = os.path.splitext(filename)[0]  # 获取 GIF 文件名（不带扩展名）
                    gif_output_folder = os.path.join(path_out, gif_name)  # 创建 GIF 文件名对应的文件夹
                    if not os.path.exists(gif_output_folder):
                        os.makedirs(gif_output_folder)

                    # 提取每一帧并保存
                    for frame in range(img.n_frames):
                        img.seek(frame)
                        frame_img = img.copy()

                        # 保存每一帧
                        frame_filename = f"{gif_name}_frame_{frame + 1}.png"  # 帧文件名
                        frame_output_path = os.path.join(gif_output_folder, frame_filename)
                        frame_img.save(frame_output_path)
                        print(f"已保存 GIF 帧: {frame_output_path}")

            except Exception as e:
                print(f"处理 GIF 文件 {file_path} 时出错: {e}")


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        "path_in": r"D:\test\gifs",
        "path_out": r"D:\test\gif_frames",
    }
    extract_frames_from_gif(config)
