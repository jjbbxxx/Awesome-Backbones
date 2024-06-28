import os
import sys

sys.path.insert(0, os.getcwd())
import argparse

import copy
import numpy as np
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score, precision_score
import matplotlib.pyplot as plt
from numpy import mean
from tqdm import tqdm
from terminaltables import AsciiTable

import torch
from torch.utils.data import DataLoader
from torch.nn.parallel import DataParallel
import time
import csv

from utils.dataloader import Mydataset, collate
from utils.train_utils import get_info, file2dict
from models.build import BuildNet
from core.evaluations import evaluate
from utils.inference import init_model


def get_metrics_output(eval_results, metrics_output, classes_names, indexs, APs, avg_inference_time):
    f = open(metrics_output, 'a', newline='')
    writer = csv.writer(f)

    p_r_f1 = [['Classes', 'Precision', 'Recall', 'F1 Score', 'Average Precision']]
    for i in range(len(classes_names)):
        data = []
        data.append(classes_names[i])
        data.append('{:.2f}'.format(eval_results.get('precision')[indexs[i]]))
        data.append('{:.2f}'.format(eval_results.get('recall')[indexs[i]]))
        data.append('{:.2f}'.format(eval_results.get('f1_score')[indexs[i]]))
        data.append('{:.2f}'.format(APs[indexs[i]] * 100))
        p_r_f1.append(data)
    TITLE = 'Classes Results'
    TABLE_DATA_1 = tuple(p_r_f1)
    table_instance = AsciiTable(TABLE_DATA_1, TITLE)
    print()
    print(table_instance.table)
    writer.writerows(TABLE_DATA_1)
    writer.writerow([])
    print()

    TITLE = 'Total Results'
    TABLE_DATA_2 = (
        ('Top-1 Acc', 'Top-5 Acc', 'Mean Precision', 'Mean Recall', 'Mean F1 Score', 'Average Inference Time (s)'),
        ('{:.2f}'.format(eval_results.get('accuracy_top-1', 0.0)),
         '{:.2f}'.format(eval_results.get('accuracy_top-5', 100.0)),
         '{:.2f}'.format(mean(eval_results.get('precision', 0.0))),
         '{:.2f}'.format(mean(eval_results.get('recall', 0.0))),
         '{:.2f}'.format(mean(eval_results.get('f1_score', 0.0))), '{:.6f}'.format(avg_inference_time)),
    )
    table_instance = AsciiTable(TABLE_DATA_2, TITLE)
    print(table_instance.table)
    writer.writerows(TABLE_DATA_2)
    writer.writerow([])
    print()

    writer_list = []
    writer_list.append([' '] + [str(c) for c in classes_names])
    for i in range(len(eval_results.get('confusion'))):
        writer_list.append([classes_names[i]] + [str(x) for x in eval_results.get('confusion')[i]])
    TITLE = 'Confusion Matrix'
    TABLE_DATA_3 = tuple(writer_list)
    table_instance = AsciiTable(TABLE_DATA_3, TITLE)
    print(table_instance.table)
    writer.writerows(TABLE_DATA_3)
    print()


def get_prediction_output(preds, targets, image_paths, classes_names, indexs, prediction_output, inference_times):
    nums = len(preds)
    with open(prediction_output, 'a', newline='') as f:
        writer = csv.writer(f)

        # 添加调试信息
        print(f"Writing {nums} predictions to {prediction_output}")

        results = [['File', 'Pre_label', 'True_label', 'Success', 'Inference Time (s)']]
        results[0].extend(classes_names)

        for i in range(nums):
            temp = [image_paths[i]]
            pred_label = classes_names[indexs[torch.argmax(preds[i]).item()]]
            true_label = classes_names[indexs[targets[i].item()]]
            success = True if pred_label == true_label else False
            class_score = preds[i].tolist()
            temp.extend([pred_label, true_label, success, '{:.6f}'.format(inference_times[i])])
            temp.extend(class_score)
            results.append(temp)

        writer.writerows(results)

        # 添加调试信息
        print(f"Successfully wrote predictions to {prediction_output}")


def plot_ROC_curve(preds, targets, classes_names, savedir):
    rows = len(targets)
    cols = len(preds[0])
    ROC_output = os.path.join(savedir, 'ROC')
    PR_output = os.path.join(savedir, 'P-R')
    os.makedirs(ROC_output)
    os.makedirs(PR_output)
    APs = []
    for j in range(cols):
        gt, pre, pre_score = [], [], []
        for i in range(rows):
            if targets[i].item() == j:
                gt.append(1)
            else:
                gt.append(0)

            if torch.argmax(preds[i]).item() == j:
                pre.append(1)
            else:
                pre.append(0)

            pre_score.append(preds[i][j].item())

        # ROC
        ROC_csv_path = os.path.join(ROC_output, classes_names[j] + '.csv')
        ROC_img_path = os.path.join(ROC_output, classes_names[j] + '.png')
        ROC_f = open(ROC_csv_path, 'a', newline='')
        ROC_writer = csv.writer(ROC_f)
        ROC_results = []

        FPR, TPR, threshold = roc_curve(targets.tolist(), pre_score, pos_label=j)

        AUC = auc(FPR, TPR)

        ROC_results.append(['AUC', AUC])
        ROC_results.append(['FPR'] + FPR.tolist())
        ROC_results.append(['TPR'] + TPR.tolist())
        ROC_results.append(['Threshold'] + threshold.tolist())
        ROC_writer.writerows(ROC_results)

        plt.figure()
        plt.title(classes_names[j] + ' ROC CURVE (AUC={:.2f})'.format(AUC))
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.01])
        plt.plot(FPR, TPR, color='g')
        plt.plot([0, 1], [0, 1], color='m', linestyle='--')
        plt.savefig(ROC_img_path)

        # AP (gt为{0,1})
        AP = average_precision_score(gt, pre_score)
        APs.append(AP)

        # P-R
        PR_csv_path = os.path.join(PR_output, classes_names[j] + '.csv')
        PR_img_path = os.path.join(PR_output, classes_names[j] + '.png')
        PR_f = open(PR_csv_path, 'a', newline='')
        PR_writer = csv.writer(PR_f)
        PR_results = []

        PRECISION, RECALL, thresholds = precision_recall_curve(targets.tolist(), pre_score, pos_label=j)

        PR_results.append(['RECALL'] + RECALL.tolist())
        PR_results.append(['PRECISION'] + PRECISION.tolist())
        PR_results.append(['Threshold'] + thresholds.tolist())
        PR_writer.writerows(PR_results)

        plt.figure()
        plt.title(classes_names[j] + ' P-R CURVE (AP={:.2f})'.format(AP))
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.01])
        plt.plot(RECALL, PRECISION, color='g')
        plt.savefig(PR_img_path)

    return APs


def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate a model')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--device', help='device used for training. (Deprecated)')
    parser.add_argument(
        '--gpu-id',
        type=int,
        default=0,
        help='id of gpu to use '
             '(only applicable to non-distributed training)')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    model_cfg, train_pipeline, val_pipeline, data_cfg, lr_config, optimizer_cfg = file2dict(args.config)

    """
    创建评估文件夹、metrics文件、混淆矩阵文件
    """
    dirname = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    save_dir = os.path.join('eval_results', model_cfg.get('backbone').get('type'), dirname)
    metrics_output = os.path.join(save_dir, 'metrics_output.csv')
    prediction_output = os.path.join(save_dir, 'prediction_results.csv')
    os.makedirs(save_dir)

    """
    获取类别名以及对应索引、获取标注文件
    """
    classes_map = 'datas/annotations.txt'
    test_annotations = 'datas/test.txt'
    classes_names, indexs = get_info(classes_map)
    with open(test_annotations, encoding='utf-8') as f:
        test_datas = f.readlines()

    """
    生成模型、加载权重
    """
    if args.device is not None:
        device = torch.device(args.device)
    else:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = BuildNet(model_cfg)
    if device != torch.device('cpu'):
        model = DataParallel(model, device_ids=[args.gpu_id])
    model = init_model(model, data_cfg, device=device, mode='eval')

    """
    制作测试集并喂入Dataloader
    """
    val_pipeline = copy.deepcopy(train_pipeline)
    test_dataset = Mydataset(test_datas, val_pipeline)
    test_loader = DataLoader(test_dataset, shuffle=True, batch_size=data_cfg.get('batch_size'),
                             num_workers=data_cfg.get('num_workers'), pin_memory=True, collate_fn=collate)

    """
    计算Precision、Recall、F1 Score、Confusion matrix
    """
    inference_times = []
    preds, targets, image_paths = [], [], []
    with torch.no_grad():
        with tqdm(total=len(test_datas) // data_cfg.get('batch_size')) as pbar:
            for _, batch in enumerate(test_loader):
                images, target, image_path = batch
                start_time = time.time()
                outputs = model(images.to(device), return_loss=False)
                end_time = time.time()
                inference_times.extend([end_time - start_time] * images.size(0))  # 确保记录每个样本的推理时间
                preds.append(outputs)
                targets.append(target.to(device))
                image_paths.extend(image_path)
                pbar.update(1)

    avg_inference_time = sum(inference_times) / len(inference_times)

    eval_results = evaluate(torch.cat(preds), torch.cat(targets), data_cfg.get('test').get('metrics'),
                            data_cfg.get('test').get('metric_options'))

    APs = plot_ROC_curve(torch.cat(preds), torch.cat(targets), classes_names, save_dir)
    get_metrics_output(eval_results, metrics_output, classes_names, indexs, APs, avg_inference_time)
    get_prediction_output(torch.cat(preds), torch.cat(targets), image_paths, classes_names, indexs, prediction_output,
                          inference_times)


if __name__ == "__main__":
    main()