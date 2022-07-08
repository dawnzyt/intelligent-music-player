import os
import re
import shutil
import time
from datetime import datetime, timedelta
import argparse
import functools
import numpy as np
import torch
from torch.nn import DataParallel
from torch.optim.lr_scheduler import StepLR
from torch.utils.data import DataLoader
from torchsummary import summary

from utils.reader import CustomDataset
from utils.arcmargin import ArcNet
from utils.resnet import resnet34
from utils.utility import add_arguments, print_arguments

#  输入参数
parser = argparse.ArgumentParser(description=__doc__)
add_arg = functools.partial(add_arguments, argparser=parser)
add_arg('gpus',             str,    '0',                      '训练使用的GPU序号，使用英文逗号,隔开，如：0,1')
add_arg('batch_size',       int,    32,                       '训练的批量大小')
add_arg('num_workers',      int,    4,                        '读取数据的线程数量')
add_arg('num_epoch',        int,    50,                       '训练的轮数')
add_arg('num_classes',      int,    400,                     '分类的类别数量')
add_arg('learning_rate',    float,  1e-3,                     '初始学习率的大小')
add_arg('weight_decay',     float,  5e-4,                     'weight_decay的大小')
add_arg('lr_step',          int,    10,                       '学习率衰减步数')
add_arg('input_shape',      str,    '(1, 257, 257)',          '数据输入的形状')
add_arg('train_list_path',  str,    'dataset/train_list.txt', '训练数据的数据列表路径')
add_arg('test_list_path',   str,    'dataset/test_list.txt',  '测试数据的数据列表路径')
add_arg('save_model',       str,    'models/',                '模型保存的路径')
add_arg('resume',           str,    None,                     '恢复训练，当为None则不使用恢复模型')
add_arg('pretrained_model', str,    None,                     '预训练模型的路径，当为None则不使用预训练模型')
args = parser.parse_args()


# 评估模型
@torch.no_grad()
def test(model, metric_fc, test_loader, device):
    '''
    功能：测试评估模型的正确率
    :param model:需评估的模型
    :param metric_fc:损失函数
    :param test_loader:测试数据
    :param device: 设备（cpu或者cuda）
    :return:分类正确率 类型为float
    '''
    accuracies = []
    for batch_id, (spec_mag, label) in enumerate(test_loader):
        spec_mag = spec_mag.to(device)
        label = label.to(device).long()
        feature = model(spec_mag)
        output = metric_fc(feature, label)
        output = output.data.cpu().numpy()
        output = np.argmax(output, axis=1)
        label = label.data.cpu().numpy()
        acc = np.mean((output == label).astype(int))
        accuracies.append(acc.item())
    return float(sum(accuracies) / len(accuracies))


# 保存模型
def save_model(args, model, metric_fc, optimizer, epoch_id):
    '''
    功能：将训练好的模型参数以及其优化器、随时函数和训练次数等信息保存为文件
    :param args:参数列表
    :param model: 训练的模型
    :param metric_fc: 使用的损失函数
    :param optimizer: 使用的优化器
    :param epoch_id:标记训练次数
    :return:无
    '''
    model_params_path = os.path.join(args.save_model, 'epoch_%d' % epoch_id)
    if not os.path.exists(model_params_path):
        os.makedirs(model_params_path)
    # 保存模型参数和优化方法参数
    torch.save(model.state_dict(), os.path.join(model_params_path, 'model_params.pth'))
    torch.save(metric_fc.state_dict(), os.path.join(model_params_path, 'metric_fc_params.pth'))
    torch.save(optimizer.state_dict(), os.path.join(model_params_path, 'optimizer.pth'))
    # 删除旧的模型
    old_model_path = os.path.join(args.save_model, 'epoch_%d' % (epoch_id - 3))
    if os.path.exists(old_model_path):
        shutil.rmtree(old_model_path)
    # 保存整个模型和参数
    all_model_path = os.path.join(args.save_model, 'resnet34.pth')
    if not os.path.exists(os.path.dirname(all_model_path)):
        os.makedirs(os.path.dirname(all_model_path))
    torch.jit.save(torch.jit.script(model), all_model_path)


def train():
    '''
    功能：通过调用以上连个函数完成对数据集的训练、评估和保存
    :return: 无
    '''
    #  GPU型号
    #  args = parser.parse_args() H37
    device_ids = [int(i) for i in args.gpus.split(',')]
    # 数据输入的形状
    # eval实现字符串转矩阵的功能
    input_shape = eval(args.input_shape)
    # 获取数据
    train_dataset = CustomDataset(args.train_list_path, model='train', spec_len=input_shape[2])
    # from utils.reader import CustomDataset
    train_loader = DataLoader(dataset=train_dataset,
                              batch_size=args.batch_size * len(device_ids),
                              shuffle=True,
                              num_workers=args.num_workers)
    test_dataset = CustomDataset(args.test_list_path, model='test', spec_len=input_shape[2])
    test_loader = DataLoader(dataset=test_dataset, batch_size=args.batch_size, num_workers=args.num_workers)

    # device = torch.device("cuda")
    device = torch.device("cuda" if torch.cuda.is_available()else"cpu")
    # 获取模型
    model = resnet34()
    metric_fc = ArcNet(512, args.num_classes)
    # from utils.arcmargin import ArcNet
    # 多个GPU分开训练
    if len(args.gpus.split(',')) > 1:
        model = DataParallel(model, device_ids=device_ids, output_device=device_ids[0])
        metric_fc = DataParallel(metric_fc, device_ids=device_ids, output_device=device_ids[0])
        # from torch.nn import DataParallel

    model.to(device)
    # device = torch.device("cuda")
    metric_fc.to(device)
    if len(args.gpus.split(',')) > 1:
        summary(model.module, input_shape)
    else:
        summary(model, input_shape)

    # 初始化epoch数
    last_epoch = 0
    # 获取优化方法
    optimizer = torch.optim.SGD([{'params': model.parameters()}, {'params': metric_fc.parameters()}],
                                lr=args.learning_rate, momentum=0.9, weight_decay=args.weight_decay)
    # 获取学习率衰减函数
    scheduler = StepLR(optimizer, step_size=args.lr_step, gamma=0.1, verbose=True)

    # 获取损失函数
    criterion = torch.nn.CrossEntropyLoss()

    # 加载模型参数和优化方法参数
    if args.resume:
        optimizer_state = torch.load(os.path.join(args.resume, 'optimizer.pth'))
        optimizer.load_state_dict(optimizer_state)
        # 获取预训练的epoch数
        last_epoch = int(re.findall('(\d+)', args.resume)[-1])
        if len(device_ids) > 1:
            model.module.load_state_dict(torch.load(os.path.join(args.resume, 'model_params.pth')))
            metric_fc.module.load_state_dict(torch.load(os.path.join(args.resume, 'metric_fc_params.pth')))
        else:
            model.load_state_dict(torch.load(os.path.join(args.resume, 'model_params.pth')))
            metric_fc.load_state_dict(torch.load(os.path.join(args.resume, 'metric_fc_params.pth')))
        print('成功加载模型参数和优化方法参数')

    # 开始训练
    sum_batch = len(train_loader) * (args.num_epoch - last_epoch)
    for epoch_id in range(last_epoch, args.num_epoch):
        for batch_id, data in enumerate(train_loader):
            start = time.time()
            data_input, label = data
            data_input = data_input.to(device)
            label = label.to(device).long()
            feature = model(data_input)
            output = metric_fc(feature, label)
            loss = criterion(output, label)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if batch_id % 100 == 0:
                output = output.data.cpu().numpy()
                output = np.argmax(output, axis=1)
                label = label.data.cpu().numpy()
                acc = np.mean((output == label).astype(int))
                eta_sec = ((time.time() - start) * 1000) * (sum_batch - (epoch_id - last_epoch) * len(train_loader) - batch_id)
                eta_str = str(timedelta(seconds=int(eta_sec / 1000)))
                print('[%s] Train epoch %d, batch: %d/%d, loss: %f, accuracy: %f, lr: %f, eta: %s' % (
                    datetime.now(), epoch_id, batch_id, len(train_loader), loss.item(), acc.item(), scheduler.get_lr()[0], eta_str))

        scheduler.step()
        # 开始评估
        model.eval()
        print('='*70)
        accuracy = test(model, metric_fc, test_loader, device)
        model.train()
        print('[{}] Test epoch {} Accuracy {:.5}'.format(datetime.now(), epoch_id, accuracy))
        print('='*70)

        # 保存模型
        if len(device_ids) > 1:
            save_model(args, model.module, metric_fc.module, optimizer, epoch_id)
        else:
            save_model(args, model, metric_fc, optimizer, epoch_id)


if __name__ == '__main__':
    #  获取GPU环境变量
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpus
    #  输出参数
    print_arguments(args)
    train()
