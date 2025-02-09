from PIL import Image
import os


def img_cut(input_json):
    # 从输入的 JSON 中获取必要的参数
    path_in = input_json.get("path_in")
    path_out = input_json.get("path_out")
    output_width = input_json.get("output_width")
    output_height = input_json.get("output_hight")
    keep_aspect_ratio = input_json.get("keep_aspect_ratio", False)

    # 检查输入路径和输出路径是否存在
    if not os.path.exists(path_in):
        print(f"输入路径 {path_in} 不存在，请检查。")
        return
    if not os.path.exists(path_out):
        os.makedirs(path_out)

    # 遍历输入路径下的所有文件
    for filename in os.listdir(path_in):
        file_path = os.path.join(path_in, filename)
        # 检查文件是否为图片文件
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                # 打开图片
                with Image.open(file_path) as img:
                    if keep_aspect_ratio:
                        # 保持原比例缩放
                        width, height = img.size
                        aspect_ratio = width / height
                        target_ratio = output_width / output_height

                        if aspect_ratio > target_ratio:
                            # 图片更宽，按高度缩放
                            new_height = output_height
                            new_width = int(new_height * aspect_ratio)
                        else:
                            # 图片更高，按宽度缩放
                            new_width = output_width
                            new_height = int(new_width / aspect_ratio)

                        img = img.resize((new_width, new_height), Image.LANCZOS)

                        # 计算裁剪的起始位置
                        left = (new_width - output_width) // 2
                        top = (new_height - output_height) // 2
                        right = left + output_width
                        bottom = top + output_height

                        # 裁剪图片
                        img = img.crop((left, top, right, bottom))
                    else:
                        # 直接缩放图片
                        img = img.resize((output_width, output_height), Image.LANCZOS)

                    # 构建输出文件的完整路径
                    output_file_path = os.path.join(path_out, filename)
                    # 保存处理后的图片
                    img.save(output_file_path)
                    print(f"已处理并保存图片: {output_file_path}")
            except Exception as e:
                print(f"处理图片 {file_path} 时出错: {e}")