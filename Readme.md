# 基于MobileNet v3的图片分类方法

## 0	Reference

[保姆级使用PyTorch训练与评估自己的MobileNetV2网络教程-CSDN博客](https://blog.csdn.net/zzh516451964zzh/article/details/124478681)

## 1	注意事项

1. 首先执行 `tools/get_annotation.py` ，因为写入的划分路径为绝对路径（暂未修改好）
1. 使用`python`在cmd中执行

## 2	目前已完成的训练模型：

- [x] MobileNet v3, 100 epoches, 64 batch_size
- [x] Vision Transformer32, 93 epochs, 32batch_size
- [ ] resnet
- [ ] vgg

## 3	后续工作

### streamlit

使用streamlit将项目部署到网页端，方便用户使用。
