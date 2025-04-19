import numpy as np
import librosa
from librosa import feature


class MFCCExtractor:
    """MFCC 特徵提取類"""
    
    def __init__(self, sampling_rate=16000, n_mfcc=13, window_size=0.025, 
                 hop_length=0.01, n_fft=None, include_delta=True, 
                 include_delta_delta=True, preemphasis=0.97):
        """
        初始化 MFCC 特徵提取器
        
        參數:
            sampling_rate (int): 採樣率
            n_mfcc (int): MFCC 係數數量
            window_size (float): 窗口大小（秒）
            hop_length (float): 步長（秒）
            n_fft (int, optional): FFT 窗口大小，如果為None，設為window_size*sampling_rate
            include_delta (bool): 是否包括一階差分
            include_delta_delta (bool): 是否包括二階差分
            preemphasis (float): 預加重係數
        """
        self.sampling_rate = sampling_rate
        self.n_mfcc = n_mfcc
        self.window_size = window_size
        self.hop_length = hop_length
        self.n_fft = int(window_size * sampling_rate) if n_fft is None else n_fft
        self.win_length = int(window_size * sampling_rate)
        self.hop_length_samples = int(hop_length * sampling_rate)
        self.include_delta = include_delta
        self.include_delta_delta = include_delta_delta
        self.preemphasis = preemphasis
    
    def _preemphasis_filter(self, audio):
        """
        應用預加重濾波器
        
        參數:
            audio (numpy.ndarray): 音頻信號
            
        返回:
            numpy.ndarray: 預加重後的音頻
        """
        return np.append(audio[0], audio[1:] - self.preemphasis * audio[:-1])
    
    def extract(self, audio):
        """
        從音頻提取 MFCC 特徵
        
        參數:
            audio (numpy.ndarray): 音頻信號
            
        返回:
            numpy.ndarray: MFCC 特徵矩陣，形狀為 (n_frames, n_features)
        """
        # 預加重
        if self.preemphasis > 0:
            audio = self._preemphasis_filter(audio)
        
        # 提取 MFCC
        mfcc_features = feature.mfcc(
            y=audio, 
            sr=self.sampling_rate,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            win_length=self.win_length,
            hop_length=self.hop_length_samples
        )
        
        # 轉置使每行代表一幀
        mfcc_features = mfcc_features.T
        
        features_list = [mfcc_features]
        
        # 計算一階差分（delta）
        if self.include_delta:
            delta = librosa.feature.delta(mfcc_features.T).T
            features_list.append(delta)
        
        # 計算二階差分（delta-delta）
        if self.include_delta_delta:
            delta_delta = librosa.feature.delta(mfcc_features.T, order=2).T
            features_list.append(delta_delta)
        
        # 合併所有特徵
        combined_features = np.hstack(features_list)
        
        return combined_features
    
    def extract_from_file(self, file_path):
        """
        從文件提取 MFCC 特徵
        
        參數:
            file_path (str): 音頻文件路徑
            
        返回:
            numpy.ndarray: MFCC 特徵矩陣
            float: 文件時長（秒）
        """
        audio, _ = librosa.load(file_path, sr=self.sampling_rate, mono=True)
        duration = len(audio) / self.sampling_rate
        features = self.extract(audio)
        return features, duration
    
    def extract_from_segments(self, audio, segments):
        """
        從語音區段提取 MFCC 特徵
        
        參數:
            audio (numpy.ndarray): 音頻信號
            segments (list): 語音區段的時間戳 [(start1, end1), (start2, end2), ...]
            
        返回:
            list: 每個區段的特徵 [(features1, duration1), (features2, duration2), ...]
        """
        segment_features = []
        
        for start, end in segments:
            start_sample = int(start * self.sampling_rate)
            end_sample = int(end * self.sampling_rate)
            segment_audio = audio[start_sample:end_sample]
            
            # 如果區段太短，可能無法提取特徵
            if len(segment_audio) < self.win_length:
                continue
                
            duration = (end - start)
            features = self.extract(segment_audio)
            segment_features.append((features, duration))
            
        return segment_features
    
    def get_feature_dimension(self):
        """
        獲取特徵維度
        
        返回:
            int: 特徵向量的維度
        """
        base_dim = self.n_mfcc
        total_dim = base_dim
        
        if self.include_delta:
            total_dim += base_dim
            
        if self.include_delta_delta:
            total_dim += base_dim
            
        return total_dim


if __name__ == "__main__":
    # 使用示例
    mfcc_extractor = MFCCExtractor(
        sampling_rate=16000,
        n_mfcc=13,
        include_delta=True,
        include_delta_delta=True
    )
    
    # 從文件提取特徵
    audio_file = "path/to/audio.wav"
    features, duration = mfcc_extractor.extract_from_file(audio_file)
    
    print(f"特徵維度: {mfcc_extractor.get_feature_dimension()}")
    print(f"提取的特徵形狀: {features.shape}")
    print(f"音頻時長: {duration}秒") 