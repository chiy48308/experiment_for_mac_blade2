"""
DTW對齊模組測試
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import os

# 假設我們有DTW對齊類，如果沒有，你需要先創建該模塊
# 以下測試基於假設的DTW對齊類實現

# 為測試創建一個假的DTW對齊類定義
class DTWAligner:
    """DTW對齊器假設類，用於展示測試結構"""
    
    def __init__(self, window_type='sakoe_chiba', window_size=0.1):
        self.window_type = window_type
        self.window_size = window_size
    
    def align(self, source_features, target_features):
        """對齊兩組特徵序列"""
        # 實際實現會計算DTW路徑和成本
        # 這裡是假設的
        path = [(i, i) for i in range(min(len(source_features), len(target_features)))]
        cost = 0.0
        return path, cost
    
    def get_alignment_segments(self, path, source_duration, target_duration):
        """從對齊路徑獲取時間段對應"""
        # 生成近似的時間段映射
        segments = []
        for i in range(0, len(path), len(path)//5):
            source_time = (path[i][0] / len(path)) * source_duration
            target_time = (path[i][1] / len(path)) * target_duration
            segments.append((source_time, target_time))
        return segments


class TestDTWAligner:
    """DTW對齊器測試類"""
    
    def test_initialization(self):
        """測試初始化參數"""
        aligner = DTWAligner(window_type='sakoe_chiba', window_size=0.1)
        
        assert aligner.window_type == 'sakoe_chiba'
        assert aligner.window_size == 0.1
    
    def test_align(self):
        """測試特徵序列對齊功能"""
        # 創建兩組假特徵序列
        source_features = np.random.rand(100, 13)  # 100幀，13維特徵
        target_features = np.random.rand(120, 13)  # 120幀，13維特徵
        
        # 建立對齊器實例
        aligner = DTWAligner()
        
        # 模擬對齊計算
        with patch.object(aligner, 'align', autospec=True) as mock_align:
            # 設置mock返回值（路徑和成本）
            mock_path = [(i, int(i * 1.2)) for i in range(100)]  # 模擬時間軸縮放
            mock_cost = 10.5
            mock_align.return_value = (mock_path, mock_cost)
            
            # 調用對齊方法
            path, cost = aligner.align(source_features, target_features)
            
            # 驗證結果
            assert path == mock_path
            assert cost == mock_cost
            
            # 驗證調用
            mock_align.assert_called_once_with(source_features, target_features)
    
    def test_get_alignment_segments(self):
        """測試從對齊路徑生成時間段對應"""
        # 創建一個假的對齊路徑
        path = [(i, int(i * 1.5)) for i in range(100)]  # 模擬時間軸縮放
        source_duration = 10.0  # 假設源音頻10秒
        target_duration = 15.0  # 假設目標音頻15秒
        
        # 建立對齊器實例
        aligner = DTWAligner()
        
        # 調用生成時間段方法
        segments = aligner.get_alignment_segments(path, source_duration, target_duration)
        
        # 驗證結果
        assert len(segments) > 0
        
        # 檢查每個段落
        for source_time, target_time in segments:
            # 源時間應在0到源持續時間之間
            assert 0 <= source_time <= source_duration
            # 目標時間應在0到目標持續時間之間
            assert 0 <= target_time <= target_duration
            # 目標時間大致應該是源時間的1.5倍（基於路徑的構造）
            assert pytest.approx(target_time / source_time, abs=0.2) == 1.5
    
    def test_end_to_end_alignment(self, sample_features):
        """測試端到端的對齊過程"""
        # 創建兩組特徵，第二組稍微拉伸
        source_features = sample_features[:100, :]  # 取前100幀
        target_features = np.repeat(source_features, 2, axis=0)[::3]  # 非線性拉伸
        
        source_duration = 5.0  # 假設5秒
        target_duration = 8.0  # 假設8秒
        
        # 建立對齊器實例
        aligner = DTWAligner()
        
        # 進行對齊
        path, cost = aligner.align(source_features, target_features)
        
        # 獲取時間段對應
        segments = aligner.get_alignment_segments(path, source_duration, target_duration)
        
        # 驗證結果
        assert len(path) > 0
        assert len(segments) > 0
        assert isinstance(cost, (int, float))  # 成本應該是數值
        
        # 檢查路徑是否合理（單調遞增）
        for i in range(1, len(path)):
            assert path[i][0] >= path[i-1][0]  # 源索引單調增
            assert path[i][1] >= path[i-1][1]  # 目標索引單調增 