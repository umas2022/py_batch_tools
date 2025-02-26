import os
from PIL import Image

def images_to_bmp(input_json):
    # 获取输入和输出路径
    path_in = input_json["path_in"]
    path_out = input_json["path_out"]

    # 如果输出路径不存在，则创建它
    if not os.path.exists(path_out):
        os.makedirs(path_out)

    # 遍历输入路径下的所有文件
    for filename in os.listdir(path_in):
        # 获取文件的完整路径
        file_path = os.path.join(path_in, filename)

        # 检查文件是否为图片（可以根据需要扩展支持的格式）
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            try:
                # 打开图片
                with Image.open(file_path) as img:
                    # 构造输出文件路径
                    output_filename = os.path.splitext(filename)[0] + '.bmp'
                    output_path = os.path.join(path_out, output_filename)

                    # 将图片保存为BMP格式
                    img.save(output_path, 'BMP')
                    print(f"Converted {filename} to {output_filename}")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")
        else:
            print(f"Skipping non-image file: {filename}")

# 示例调用
input_json = {
    "path_in": r"E:\ws-code\test\test_in",
    "path_out": r"E:\ws-code\test\test_out",
}

images_to_bmp(input_json)