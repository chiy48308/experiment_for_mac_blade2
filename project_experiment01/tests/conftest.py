"""
Pytest 配置文件，定義通用測試 fixtures
"""
import os
import sys
import pytest
import numpy as np

# 確保可以在測試中正確引入專案模組
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def sample_audio():
    """生成一個測試用的音頻樣本"""
    sampling_rate = 16000
    duration = 2  # 秒
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    
    # 生成包含兩個頻率的正弦波 (模擬語音片段)
    # 0.5-1.0 秒 和 1.5-2.0 秒為語音
    audio = np.zeros_like(t)
    
    # 第一個語音段 (0.5-1.0 秒)
    speech_indices1 = np.logical_and(t >= 0.5, t < 1.0)
    audio[speech_indices1] = 0.5 * np.sin(2 * np.pi * 440 * t[speech_indices1])
    
    # 第二個語音段 (1.5-2.0 秒)
    speech_indices2 = np.logical_and(t >= 1.5, t < 2.0)
    audio[speech_indices2] = 0.5 * np.sin(2 * np.pi * 880 * t[speech_indices2])
    
    # 添加少量噪聲
    np.random.seed(42)
    noise = np.random.normal(0, 0.01, len(audio))
    audio = audio + noise
    
    return audio, sampling_rate


@pytest.fixture
def expected_vad_segments():
    """預期的VAD分割結果"""
    # 基於 sample_audio 的預期分割
    return [(0.5, 1.0), (1.5, 2.0)]


@pytest.fixture
def mock_audio_file(tmp_path):
    """創建一個臨時的音頻文件"""
    import soundfile as sf
    from scipy.io import wavfile
    
    # 創建測試音頻
    audio, sr = sample_audio()
    
    # 寫入臨時文件
    tmp_file = tmp_path / "test_audio.wav"
    wavfile.write(tmp_file, sr, (audio * 32767).astype(np.int16))
    
    return str(tmp_file)


@pytest.fixture
def sample_features():
    """生成測試用特徵矩陣"""
    # 模擬 13 維 MFCC 特徵，每秒 100 幀，共 2 秒
    np.random.seed(42)
    frames = 200
    n_mfcc = 13
    
    # 模擬 MFCC 特徵
    features = np.random.normal(0, 1, (frames, n_mfcc))
    
    return features 