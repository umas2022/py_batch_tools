from PIL import Image
import os


def images_to_gif(input_json):
    # 从输入的 JSON 中获取必要的参数
    input_path = input_json.get("path_in")
    output_path = input_json.get("path_out")
    output_name = input_json.get("output_name")
    frame_duration = input_json.get("frame_duration", 100)  # 每一帧的持续时间，单位为毫秒，默认 100ms
    loop = input_json.get("loop", 0)  # 循环次数，0 表示无限循环

    # 检查输入路径是否存在
    if not os.path.exists(input_path):
        print(f"输入路径 {input_path} 不存在。")
        return

    # 组合完整的输出文件路径
    full_output_path = os.path.join(output_path, output_name)

    # 检查并创建输出目录
    output_dir = os.path.dirname(full_output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取输入路径下的所有图片文件
    image_files = []
    for filename in os.listdir(input_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_files.append(os.path.join(input_path, filename))

    # 按文件名排序
    image_files.sort()

    if not image_files:
        print(f"输入路径 {input_path} 下未找到图片文件。")
        return

    images = []
    for image_file in image_files:
        try:
            img = Image.open(image_file)
            images.append(img)
        except Exception as e:
            print(f"打开图片 {image_file} 时出错: {e}")

    if not images:
        print("没有有效的图片可以合成 GIF。")
        return

    # 保存为 GIF
    try:
        images[0].save(full_output_path, save_all=True, append_images=images[1:],
                       duration=frame_duration, loop=loop)
        print(f"已将图片合成 GIF 并保存到 {full_output_path}")
    except Exception as e:
        print(f"合成 GIF 时出错: {e}")


# ===================== 示例调用 =====================

if __name__ == "__main__":
    config = {
        "path_in": r"D:\test\input_images",
        "path_out": r"D:\test\output_gif",
        "output_name": "output.gif",
        "frame_duration": 100,
        "loop": 0,
    }
    images_to_gif(config)
