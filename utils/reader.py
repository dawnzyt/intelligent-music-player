import librosa
import numpy as np
from torch.utils import data


# 加载并预处理音频
def load_audio(audio_path, mode='train', win_length=400, sr=16000, hop_length=160, n_fft=512, spec_len=257):
    # 读取音频数据
    # n_fft 用零填充后的窗户信号的长度
    # hop_length 相邻傅里叶变换列之间的音频样本数。
    # win_length 每个音频框架都用长度win_length的窗口，然后用零填充以匹配n_fft

    wav, sr_ret = librosa.load(audio_path, sr=sr)
    # 数据拼接
    if mode == 'train':
        extended_wav = np.append(wav, wav)
        # 将wav文件拓展 np.append 为合并两个数组
        if np.random.random() < 0.3:
            extended_wav = extended_wav[::-1]
            # 有0.3的概率将数组倒置
    else:
        extended_wav = np.append(wav, wav[::-1])
    # 计算短时傅里叶变换
    linear = librosa.stft(extended_wav, n_fft=n_fft, win_length=win_length, hop_length=hop_length)
    mag, _ = librosa.magphase(linear)
    freq, freq_time = mag.shape
    assert freq_time >= spec_len, "非静音部分长度不能低于1.3s"
    if mode == 'train':
        # 随机裁剪
        rand_time = np.random.randint(0, freq_time - spec_len)
        spec_mag = mag[:, rand_time:rand_time + spec_len]
    else:
        spec_mag = mag[:, :spec_len]
    mean = np.mean(spec_mag, 0, keepdims=True)
    std = np.std(spec_mag, 0, keepdims=True)
    spec_mag = (spec_mag - mean) / (std + 1e-5)
    spec_mag = spec_mag[np.newaxis, :]
    return spec_mag


# 数据加载器
class CustomDataset(data.Dataset):
    def __init__(self, data_list_path, model='train', spec_len=257):
        # 地址 模型 长度
        super(CustomDataset, self).__init__()
        # 继承Dataset库
        with open(data_list_path, 'r') as f:
            self.lines = f.readlines()
            # 文件中 所有行的列表
        self.model = model
        self.spec_len = spec_len

    def __getitem__(self, idx):
        audio_path, label = self.lines[idx].replace('\n', '').split('\t')
        # 音频地址是 和标签文件中idx中将'\n'替换为''后以'\t'为标志切分
        spec_mag = load_audio(audio_path, mode=self.model, spec_len=self.spec_len)
        return spec_mag, np.array(int(label), dtype=np.int64)

    def __len__(self):
        return len(self.lines)
