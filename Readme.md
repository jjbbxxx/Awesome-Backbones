# 基于多模型的图片分类方法

## 0	Reference

[Awesome-Backbones](https://github.com/Fafa-DL/Awesome-Backbones)

## 1	注意事项

1. 首先执行 `tools/get_annotation.py` ，因为写入的划分路径为绝对路径（暂未修改好）
1. 使用`python`在cmd中运行，不要在IDE或IDE终端中运行

## 2	步骤

1. 准备好数据集，利用`split_data`和`get_annotation`进行分割和打标签
2. 在`models/`中修改对应模型参数
	1. `num_classes`修改为需要的分类数
	2. 合适的`batch_size`与`num_workers`
	3. 如果有预训练权重则添加到`pretrained_weights`并将`pretrained_flag`置为`True`
3. 运行`train.py`开始训练，结果存于`logs`文件夹中
4. 将训练好的pth文件填入配置文件的`ckpt`中
5. 运行`evaluation.py`进行评估，结果存于`eval_results`文件夹中

## 3	目前已完成的训练模型：

- [x] MobileNet v3, 100 epoches, 64 batch_size
- [x] Vision Transformer32, 93 epochs, 32 batch_size
- [x] resnet, 100 epochs, 64 batch_size
- [ ] vgg

## 4	后续工作

### streamlit

使用streamlit将项目部署到网页端，方便用户使用。
