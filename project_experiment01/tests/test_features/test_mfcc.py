"""
MFCC特徵提取模組測試
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import os

from src.features.mfcc import MFCCExtractor


class TestMFCCExtractor:
    """MFCC特徵提取器測試類"""
    
    def test_initialization(self):
        """測試初始化參數"""
        mfcc = MFCCExtractor(
            sampling_rate=16000,
            n_mfcc=13,
            window_size=0.025,
            hop_length=0.01,
            include_delta=True,
            include_delta_delta=True,
            preemphasis=0.97
        )
        
        assert mfcc.sampling_rate == 16000
        assert mfcc.n_mfcc == 13
        assert mfcc.window_size == 0.025
        assert mfcc.hop_length == 0.01
        assert mfcc.include_delta == True
        assert mfcc.include_delta_delta == True
        assert mfcc.preemphasis == 0.97
        assert mfcc.n_fft == int(0.025 * 16000)
        assert mfcc.win_length == int(0.025 * 16000)
        assert mfcc.hop_length_samples == int(0.01 * 16000)
    
    def test_preemphasis_filter(self):
        """測試預加重濾波器"""
        mfcc = MFCCExtractor(preemphasis=0.97)
        
        # 創建一個簡單的測試信號
        audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        # 應用預加重
        pre_audio = mfcc._preemphasis_filter(audio)
        
        # 手動計算預期結果
        expected = np.array([0.1, 0.2 - 0.97 * 0.1, 0.3 - 0.97 * 0.2, 0.4 - 0.97 * 0.3, 0.5 - 0.97 * 0.4])
        
        # 驗證結果
        np.testing.assert_allclose(pre_audio, expected, rtol=1e-5)
    
    @patch('librosa.feature.mfcc')
    @patch('librosa.feature.delta')
    def test_extract(self, mock_delta, mock_mfcc):
        """測試特徵提取功能"""
        # 創建模擬的mfcc特徵
        mock_mfcc_features = np.random.rand(13, 100)  # (n_mfcc, n_frames)
        mock_mfcc.return_value = mock_mfcc_features
        
        # 創建模擬的delta特徵
        mock_delta_features = np.random.rand(13, 100)
        mock_delta_delta_features = np.random.rand(13, 100)
        mock_delta.side_effect = [mock_delta_features, mock_delta_delta_features]
        
        # 建立提取器實例
        mfcc = MFCCExtractor(
            n_mfcc=13,
            include_delta=True,
            include_delta_delta=True,
            preemphasis=0.97
        )
        
        # 生成測試音頻
        audio = np.random.rand(16000)
        
        # 調用提取方法
        features = mfcc.extract(audio)
        
        # 驗證結果
        assert features.shape[1] == 13 * 3  # 13 基本特徵 + 13 delta + 13 delta-delta
        assert features.shape[0] == 100     # 幀數
        
        # 驗證調用
        mock_mfcc.assert_called_once()
        assert mock_delta.call_count == 2
    
    @patch('librosa.load')
    def test_extract_from_file(self, mock_load):
        """測試從文件提取特徵的功能"""
        # 模擬音頻加載
        mock_audio = np.random.rand(16000)
        mock_load.return_value = (mock_audio, 16000)
        
        # 模擬特徵提取
        with patch.object(MFCCExtractor, 'extract', return_value=np.random.rand(100, 39)) as mock_extract:
            # 建立提取器實例
            mfcc = MFCCExtractor(sampling_rate=16000)
            
            # 提取特徵
            features, duration = mfcc.extract_from_file("dummy_file.wav")
            
            # 驗證結果
            assert features.shape == (100, 39)
            assert duration == 1.0  # 16000樣本 / 16000採樣率 = 1秒
            
            # 驗證調用
            mock_load.assert_called_once_with("dummy_file.wav", sr=16000, mono=True)
            mock_extract.assert_called_once_with(mock_audio)
    
    def test_extract_from_segments(self, sample_audio, expected_vad_segments):
        """測試從語音段提取特徵的功能"""
        audio, sr = sample_audio
        
        # 建立提取器實例，使用簡單配置
        mfcc = MFCCExtractor(
            sampling_rate=sr,
            n_mfcc=13,
            include_delta=False,
            include_delta_delta=False,
            preemphasis=0
        )
        
        # 模擬特徵提取
        with patch.object(mfcc, 'extract', return_value=np.random.rand(50, 13)) as mock_extract:
            # 從段落提取特徵
            segment_features = mfcc.extract_from_segments(audio, expected_vad_segments)
            
            # 驗證結果
            assert len(segment_features) == len(expected_vad_segments)
            
            # 檢查每個段落的結果
            for (features, duration), (start, end) in zip(segment_features, expected_vad_segments):
                assert features.shape == (50, 13)
                assert duration == pytest.approx(end - start, abs=1e-3)
    
    def test_get_feature_dimension(self):
        """測試特徵維度計算"""
        # 只有基本特徵
        mfcc1 = MFCCExtractor(n_mfcc=13, include_delta=False, include_delta_delta=False)
        assert mfcc1.get_feature_dimension() == 13
        
        # 基本特徵 + delta
        mfcc2 = MFCCExtractor(n_mfcc=13, include_delta=True, include_delta_delta=False)
        assert mfcc2.get_feature_dimension() == 26
        
        # 基本特徵 + delta + delta-delta
        mfcc3 = MFCCExtractor(n_mfcc=13, include_delta=True, include_delta_delta=True)
        assert mfcc3.get_feature_dimension() == 39 