# -*- coding: utf-8 -*-
"""Ast_encoder.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1F206fKiqSTw5n3fzPrtfggd_J4pYGXk2

1. data 16khz 로 바꾸기
2.  normalize the input to 0 mean and 0.5 std
* You can check ast/src/get_norm_stats.py to see how we compute the stats, or you can try using our AudioSet normalization input_spec = (input_spec + 4.26) / (4.57 * 2)

* Please note that AST needs smaller learning rate
"""


# !pip install transformers[torch] datasets[audio] audiomentations

# !pip install torch torchaudio

# !pip install "transformers[sentencepiece]"
from transformers import AutoFeatureExtractor, ASTModel
import torch
import torchaudio
import os
import numpy as np

class ASTEncoder:
    def __init__(self, model_name="MIT/ast-finetuned-audioset-10-10-0.4593", sampling_rate=16000):
        self.sampling_rate = sampling_rate
        self.extractor = AutoFeatureExtractor.from_pretrained(model_name, sampling_rate=sampling_rate, do_normalize=True)  # 입력 16khz로 맞추기, normalize 진행
        self.model = ASTModel.from_pretrained(model_name)
        self.training =True
        self.output_dim = self.model.config.hidden_size

    def preprocess(self, clip_a, clip_b):


        clip_a_embeddings = []
        clip_b_embeddings = []

        for audio in clip_a:
            #두 채널인 경우 두 채널 모두 처리 : 스트레오 오디오면 2개의 좌우채널 존재
            if audio.ndim >1:
                channel_embeddings = []               
                for chanel in audio:
                    #텐서를 numpy로 변환
                    audio_np = chanel.cpu().numpy()
                    #특징 추출
                    input_values = self.extractor(audio_np, sampling_rate=self.sampling_rate)["input_values"]

                    if isinstance(input_values, list):
                        input_values = input_values[0]
                    #numpy 배열로 확실히 변환
                    input_values = np.array(input_values)
                    #텐서변환
                    input_values = torch.from_numpy(input_values).unsqueeze(0)  # (1, max_length, num_mel_bins) 형태로 변환 (차원 추가)


                    if self.training:  
                        self.model.train()
                        output = self.model(input_values).last_hidden_state
                    else:
                        self.model.eval()
                        with torch.no_grad():
                            output = self.model(input_values).last_hidden_state
                    channel_embeddings.append(output.squeeze().detach().cpu().numpy())

                clip_a_embeddings.append(np.mean(channel_embeddings, axis=0))
  
        for audio in clip_b:
            #두 채널인 경우 두 채널 모두 처리 : 스트레오 오디오면 2개의 좌우채널 존재
            if audio.ndim >1:
                channel_embeddings = []
                for chanel in audio:
                    #텐서를 numpy로 변환
                    audio_np = chanel.cpu().numpy()

                    #특징 추출
                    input_values = self.extractor(audio_np, sampling_rate=self.sampling_rate)["input_values"]

                    if isinstance(input_values, list):
                        input_values = input_values[0]

                    #numpy 배열로 확실히 변환
                    input_values = np.array(input_values)

                    #텐서변환
                    input_values = torch.from_numpy(input_values).unsqueeze(0)  # (1, max_length, num_mel_bins) 형태로 변환
                
                    
                    if self.training:  
                        self.model.train()
                        output = self.model(input_values).last_hidden_state
                    else:
                        self.model.eval()
                        with torch.no_grad():
                            output = self.model(input_values).last_hidden_state
                    channel_embeddings.append(output.squeeze().detach().cpu().numpy())
                
                    

                clip_b_embeddings.append(np.mean(channel_embeddings, axis=0))
            

        # flatten하여 2차원 텐서로 변환 (batch_size, embedding_dim)
        clip_a_embeddings = np.array(clip_a_embeddings)
        clip_b_embeddings = np.array(clip_b_embeddings)

        # 각 배치의 임베딩을 펼쳐서 차원을 flatten
        clip_a_embeddings = clip_a_embeddings.reshape(clip_a_embeddings.shape[0], -1)
        clip_b_embeddings = clip_b_embeddings.reshape(clip_b_embeddings.shape[0], -1)

        return clip_a_embeddings, clip_b_embeddings
    
    def set_eval_mode(self):
        self.model.eval()
    
    def set_train_mode(self):
        self.model.train()