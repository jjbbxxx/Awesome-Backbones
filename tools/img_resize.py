import os
from PIL import Image


def resize_image(image_path, output_path, output_size=(224, 224)):
    with Image.open(image_path) as img:
        img = img.resize(output_size, Image.ANTIALIAS)

        # 如果图像不是RGB模式，将其转换为RGB模式
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img.save(output_path)


def process_directory(input_directory, output_directory):
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                input_path = os.path.join(root, file)

                # 保持文件夹结构
                relative_path = os.path.relpath(root, input_directory)
                output_path = os.path.join(output_directory, relative_path, file)

                # 创建输出目录（如果不存在）
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                print(f"Resizing image: {input_path} -> {output_path}")
                resize_image(input_path, output_path)


if __name__ == "__main__":
    input_directory = 'datasets'  # 输入目录
    output_directory = 'datasets_resized'  # 输出目录
    process_directory(input_directory, output_directory)
