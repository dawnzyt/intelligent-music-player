import os
from utils.reader import load_audio
import torch
import numpy as np
model_path='models/resnet34.pth'
# 声纹注册
device = torch.device("cuda")
# 载入模型
model = torch.jit.load(model_path)
model.to(device)
model.eval()

def infer(audio_path):
    input_shape = (1,257,257)
    data = load_audio(audio_path, mode='infer', spec_len=input_shape[2])
    data = data[np.newaxis, :]
    data = torch.tensor(data, dtype=torch.float32, device=device)
    # 执行预测
    feature = model(data)
    return feature.data.cpu().numpy()

if __name__=='__main__':
    name_list=os.listdir('audio_db')
    Ws=[]
    for name in name_list:
        path='audio_db/'+name
        audio_name_list=os.listdir(path)
        features = []
        for audio_name in audio_name_list:
            audio_path=path+'/'+audio_name
            feature=infer(audio_path)[0]
            features.append(feature / np.linalg.norm(feature))
        W = np.sum(np.array(features), axis=0) / len(features)
        Ws.append(W)
    Ws = np.array(Ws)
    out = np.concatenate([Ws, np.expand_dims(name_list, axis=1)], axis=1)
    np.savetxt('audio_data.txt', np.c_[out], fmt='%s', delimiter=',')