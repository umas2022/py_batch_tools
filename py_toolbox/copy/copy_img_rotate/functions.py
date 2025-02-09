from PIL import Image
import os


def rotate_images(input_json):
    # 从输入的 JSON 中获取必要的参数
    input_path = input_json.get("path_in")
    output_path = input_json.get("path_out")
    angle = input_json.get("angle")

    # 检查输入路径是否存在
    if not os.path.exists(input_path):
        print(f"输入路径 {input_path} 不存在。")
        return
    # 若输出路径不存在，则创建它
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 遍历输入路径下的所有文件
    for filename in os.listdir(input_path):
        file_path = os.path.join(input_path, filename)
        # 检查文件是否为图片文件
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                # 打开图片
                with Image.open(file_path) as img:
                    # 旋转图片
                    rotated_img = img.rotate(angle, expand=True)
                    # 构建输出文件的完整路径
                    output_file_path = os.path.join(output_path, filename)
                    # 保存旋转后的图片
                    rotated_img.save(output_file_path)
                    print(f"已旋转并保存图片: {output_file_path}")
            except Exception as e:
                print(f"处理图片 {file_path} 时出错: {e}")