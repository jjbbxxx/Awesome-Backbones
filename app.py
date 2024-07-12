import subprocess
import sys
import streamlit as st
import torch
from PIL import Image
from torchvision import models, transforms
from models.build import BuildNet  # 确保这个路径与您的项目结构相匹配


# def install(package):
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])
#
#
# # 安装必要的库
# install("scipy==1.10.0")
# install("numpy==1.22.2")
# install("matplotlib==3.4.3")
# install("opencv-python")
# install("opencv-contrib-python")
# install("opencv-python-headless")
# install("albumentations==1.2.1")
# install("tqdm==4.62.3")
# install("Pillow==10.3.0")
# install("h5py==3.1.0")
# install("terminaltables==3.1.0")
# install("packaging==21.3")
# install("torch==2.0.1+cpu")
# install("torchvision==0.15.2+cpu")

# 定义模型配置
model_cfg = dict(
    backbone=dict(type='MobileNetV3', arch='small'),
    neck=dict(type='GlobalAveragePooling'),
    head=dict(
        type='StackedLinearClsHead',
        num_classes=2,
        in_channels=576,
        mid_channels=[1024],
        dropout_rate=0.2,
        act_cfg=dict(type='HSwish'),
        loss=dict(
            type='CrossEntropyLoss', loss_weight=1.0),
        init_cfg=dict(
            type='Normal', layer='Linear', mean=0., std=0.01, bias=0.),
        topk=(1, 5)))
# 加载模型
with st.spinner("模型加载中，请稍后..."):
    model = BuildNet(model_cfg).to('cpu')  # 使用BuildNet函数创建模型实例
    model.load_state_dict(torch.load('datas/mobilenet_v3_small-8427ecf0.pth', map_location='cpu'))
    model.eval()

# 文件上传器，允许上传.dat文件
upload_file = st.file_uploader('Insert image for classification', type=['png', 'jpg'])
class_labels = {
    0: "有机垃圾",
    1: "可回收垃圾",
}
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375]
    )])
if upload_file is not None:
    st.markdown("### 用户上传图片，显示如下: ")
    image = Image.open(upload_file)
    st.image(image, caption='Uploaded Image.', use_column_width=True)
    # 模型预测
    st.markdown("**请点击按钮开始分类**")
    predict = st.button("分类")
    if predict:
        batch_t = torch.unsqueeze(transform(image), 0)
        predict = model(batch_t)
        st.title("垃圾分类结果为: {}".format(class_labels[predict]))
