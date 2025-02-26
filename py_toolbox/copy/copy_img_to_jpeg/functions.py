import os
from PIL import Image

def images_to_jpeg(input_json):
    # 从输入的 JSON 中获取输入目录和输出目录
    path_in = input_json["path_in"]
    path_out = input_json["path_out"]

    # 检查输入目录是否存在
    if not os.path.exists(path_in):
        print(f"输入目录 {path_in} 不存在。")
        return

    # 如果输出目录不存在，则创建它
    if not os.path.exists(path_out):
        os.makedirs(path_out)

    # 遍历输入目录下的所有文件
    for filename in os.listdir(path_in):
        # 构建完整的文件路径
        file_path = os.path.join(path_in, filename)

        # 检查文件是否为图片文件
        if os.path.isfile(file_path):
            try:
                # 打开图片文件
                with Image.open(file_path) as img:
                    # 转换图片模式为 RGB（JPEG 不支持透明度）
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        img = img.convert('RGB')

                    # 构建输出文件的路径，将文件名改为以 .jpg 结尾
                    output_filename = os.path.splitext(filename)[0] + '.jpg'
                    output_path = os.path.join(path_out, output_filename)

                    # 保存图片为 JPEG 格式
                    img.save(output_path, 'JPEG')
                    print(f"已将 {filename} 转换为 JPEG 格式并保存到 {output_path}")
            except Exception as e:
                print(f"处理 {filename} 时出错: {e}")