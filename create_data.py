import json
import os
from random import sample
from tqdm import tqdm
import librosa
import numpy as np
from pydub import AudioSegment
from utils.reader import load_audio


# 生成数据列表
def get_data_list(infodata_path, list_path, zhvoice_path):
    '''
    对音频数据进行mp3到wav的转化，并生成训练音频列表和特使音频列表，方便模型学习时的训练和测试
    :param infodata_path: 音频数据名称信息所在文件地址
    :param list_path: 训练/测试音频名称列表保存地址
    :param zhvoice_path: 音频数据所在的地址
    :return:
    '''
    with open(infodata_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    f_train = open(os.path.join(list_path, 'train_list.txt'), 'w')
    f_test = open(os.path.join(list_path, 'test_list.txt'), 'w')

    sound_sum = 0
    speakers = []
    speakers_dict = {}
    for line in tqdm(lines):  # lines = f.readlines()
        line = json.loads(line.replace('\n', ''))
        duration_ms = line['duration_ms']
        if duration_ms < 1300:
            continue
        speaker = line['speaker']
        if speaker not in speakers:  # speakers = []
            speakers_dict[speaker] = len(speakers)
            speakers.append(speaker)
        label = speakers_dict[speaker]
#
        sound_path = os.path.join(zhvoice_path, line['index'])
        # sound_path = zhvoice_path+'/'+line['index']
        save_path = "%s.wav" % sound_path[:-4]
        if not os.path.exists(save_path):
            try:
                wav = AudioSegment.from_mp3(sound_path)
                wav.export(save_path, format="wav")
                os.remove(sound_path)
            except Exception as e:
                print('数据出错：%s, 信息：%s' % (sound_path, e))
                continue
        if sound_sum % 200 == 0:
            f_test.write('%s\t%d\n' % (save_path.replace('\\', '/'), label))
        else:
            f_train.write('%s\t%d\n' % (save_path.replace('\\', '/'), label))
        sound_sum += 1

    f_test.close()
    f_train.close()


# 删除错误音频
def remove_error_audio(data_list_path):
    '''
    功能：在音频数据列表中删除无法使用的音频数据信息
    :param data_list_path:处理音频所在路径
    :return: 无
    '''
    with open(data_list_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines1 = []
    for line in tqdm(lines):
        audio_path, _ = line.split('\t')
        try:
            spec_mag = load_audio(audio_path)
            lines1.append(line)
        except Exception as e:
            print(audio_path)
            print(e)
    with open(data_list_path, 'w', encoding='utf-8') as f:
        for line in lines1:
            f.write(line)


if __name__ == '__main__':
    get_data_list('dataset/zhvoice/text/infodata.json', 'dataset', 'dataset/zhvoice')
    remove_error_audio('dataset/train_list.txt')
    remove_error_audio('dataset/test_list.txt')
