# 測試框架使用指南

本目錄包含專案的單元測試，使用 pytest 和 mock 來測試各個模組的功能。

## 目錄結構

```
tests/
├── __init__.py            # 測試包初始化檔案
├── conftest.py            # pytest 配置和共享 fixtures
├── README.md              # 本文件
├── test_vad/              # VAD 模組測試
│   ├── __init__.py
│   └── test_webrtc.py     # WebRTC VAD 測試
├── test_features/         # 特徵提取模組測試
│   ├── __init__.py
│   └── test_mfcc.py       # MFCC 特徵提取測試
└── test_alignment/        # 對齊模組測試
    ├── __init__.py
    └── test_dtw.py        # DTW 對齊測試
```

## 運行測試

### 運行所有測試

```bash
cd project_experiment01
python -m pytest
```

### 運行特定模組的測試

```bash
# 運行所有 VAD 測試
python -m pytest tests/test_vad

# 運行 WebRTC VAD 測試
python -m pytest tests/test_vad/test_webrtc.py

# 運行特定測試方法
python -m pytest tests/test_vad/test_webrtc.py::TestWebRTCVAD::test_initialization
```

### 生成測試覆蓋率報告

```bash
# 安裝覆蓋率工具
pip install pytest-cov

# 運行測試並生成覆蓋率報告
python -m pytest --cov=src
```

## 添加新測試

### 添加新模組的測試

1. 在對應的測試目錄中創建新的測試文件，例如 `tests/test_vad/test_silero.py`
2. 使用以下模板:

```python
"""
Silero VAD模組測試
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.vad.silero import SileroVAD


class TestSileroVAD:
    """Silero VAD測試類"""
    
    def test_initialization(self):
        """測試初始化參數"""
        # 測試初始化代碼...
        
    def test_detect(self):
        """測試語音檢測功能"""
        # 測試檢測功能代碼...
```

### 使用 Fixtures

`conftest.py` 中定義了一些有用的測試 fixtures:

- `sample_audio`: 生成測試用的音頻數據
- `expected_vad_segments`: 預期的 VAD 分割結果
- `mock_audio_file`: 創建臨時音頻文件
- `sample_features`: 生成測試用特徵矩陣

示例:

```python
def test_function_with_fixtures(sample_audio, expected_vad_segments):
    audio, sr = sample_audio
    # 使用這些 fixtures 進行測試...
```

## 使用 Mock

測試中大量使用了 unittest.mock 來模擬外部依賴和複雜操作:

```python
# 基本模擬
with patch('module.function') as mock_func:
    mock_func.return_value = expected_value
    result = function_under_test()
    assert result == expected_value

# 模擬類方法
with patch.object(instance, 'method') as mock_method:
    mock_method.return_value = expected_value
    result = instance.method()
    assert result == expected_value

# 模擬複雜返回值
mock_func.side_effect = [value1, value2, value3]  # 連續調用時返回不同值

# 自定義 side_effect 函數
def custom_effect(*args, **kwargs):
    # 執行自定義邏輯...
    return result

mock_func.side_effect = custom_effect
```

## 測試原則

1. **單元測試應該獨立**：每個測試應該能夠獨立運行，不依賴其他測試的狀態。

2. **使用 mock 隔離外部依賴**：測試特定功能時，模擬其依賴以確保測試的獨立性和可靠性。

3. **覆蓋核心功能**：確保測試覆蓋所有關鍵功能和邊界條件。

4. **測試應該快速**：單元測試應該快速執行，避免耗時的操作。

5. **使用斷言檢查結果**：始終使用 assert 驗證結果，不只是檢查運行是否無錯誤。 