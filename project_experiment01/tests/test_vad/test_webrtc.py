"""
WebRTC VAD模組測試
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import os

from src.vad.webrtc import WebRTCVAD


class TestWebRTCVAD:
    """WebRTC VAD測試類"""
    
    def test_initialization(self):
        """測試初始化參數"""
        vad = WebRTCVAD(frame_size=30, aggressive_level=2, sampling_rate=16000)
        
        assert vad.frame_size == 30
        assert vad.aggressive_level == 2
        assert vad.sampling_rate == 16000
    
    def test_detect_with_sample_audio(self, sample_audio, expected_vad_segments):
        """測試語音檢測功能是否能正確識別語音段"""
        audio, sr = sample_audio
        
        # 建立VAD實例
        vad = WebRTCVAD(frame_size=30, aggressive_level=2, sampling_rate=sr)
        
        # 模擬vad.is_speech的行為，使其返回與預期匹配的結果
        with patch.object(vad.vad, 'is_speech', autospec=True) as mock_is_speech:
            # 設置mock以匹配預期的分割結果
            # 第一個語音段: 0.5-1.0秒
            # 第二個語音段: 1.5-2.0秒
            def side_effect(frame, sample_rate):
                # 簡單計算該幀對應的時間
                frame_idx = int(frame_counter[0])
                frame_counter[0] += 1
                
                # 30ms 每幀的時間對應
                frame_time = frame_idx * 0.03
                
                # 如果當前幀時間在預期的語音段內，返回True
                if (0.5 <= frame_time < 1.0) or (1.5 <= frame_time < 2.0):
                    return True
                return False
            
            # 用於跟踪調用次數
            frame_counter = [0]
            mock_is_speech.side_effect = side_effect
            
            # 執行檢測
            segments = vad.detect(audio)
            
            # 驗證結果
            assert len(segments) == len(expected_vad_segments)
            
            # 允許0.1秒的誤差（由於幀大小和合併可能導致的不精確）
            for i, (start, end) in enumerate(segments):
                exp_start, exp_end = expected_vad_segments[i]
                assert abs(start - exp_start) < 0.1
                assert abs(end - exp_end) < 0.1
    
    def test_process_file(self, mock_audio_file, expected_vad_segments):
        """測試處理音頻文件的功能"""
        # 建立VAD實例
        vad = WebRTCVAD(frame_size=30, aggressive_level=2)
        
        # 使用模擬的detect方法
        with patch.object(vad, 'detect', return_value=expected_vad_segments):
            segments, audio = vad.process_file(mock_audio_file)
            
            # 驗證結果
            assert segments == expected_vad_segments
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
    
    def test_export_segments(self, mock_audio_file, expected_vad_segments, tmp_path):
        """測試導出語音段落的功能"""
        output_dir = str(tmp_path / "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 建立VAD實例
        vad = WebRTCVAD(frame_size=30, aggressive_level=2)
        
        # 模擬process_file方法
        with patch.object(vad, 'process_file', return_value=(expected_vad_segments, np.zeros(32000))):
            # 模擬librosa.output.write_wav函數
            with patch('librosa.output.write_wav') as mock_write_wav:
                output_files = vad.export_segments(mock_audio_file, output_dir)
                
                # 驗證結果
                assert len(output_files) == len(expected_vad_segments)
                assert mock_write_wav.call_count == len(expected_vad_segments) 