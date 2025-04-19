# 語音評分實驗框架使用指南

## 1. 專案概述

本專案實現了一個模組化的語音評分實驗框架，用於研究不同語音活動偵測（VAD）方法與特徵提取策略對語音切割準確性與評分系統效能的影響。整體框架支持以下實驗組件的靈活替換和配置：

- 語音活動偵測（VAD）模組
- 特徵提取模組
- 對齊模組
- 評分模型
- 評估指標

實驗採用「Stack」的概念組織，每個Stack是一組特定的組件組合，便於對比不同方法的效果。

## 2. 安裝與環境配置

### 環境需求
- Python 3.8+
- 相依套件列表在 `requirements.txt`

### 安裝步驟
```bash
# 1. 克隆專案 (如適用)
git clone <repository-url>
cd project_experiment01

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt
```

## 3. 主執行實驗入口

項目的主要執行入口是 `main.py`，支持以下使用方式：

```bash
# 執行所有Stack實驗
python main.py

# 執行特定Stack
python main.py -s stack1

# 自定義實驗名稱
python main.py -n my_experiment_name

# 指定配置文件
python main.py -c config/my_custom_config.yaml

# 指定數據集配置
python main.py -d data/my_dataset_config.yaml
```

命令行參數說明：
- `-c`, `--config`: 實驗配置文件路徑（默認：`config/experiment_config.yaml`）
- `-s`, `--stack`: 僅運行指定Stack
- `-n`, `--name`: 實驗名稱（用於結果保存和識別）
- `-d`, `--data`: 數據集配置文件（默認：`data/dataset_config.yaml`）

## 4. 可替換模組詳解

### 4.1 語音活動偵測（VAD）模組
位置：`src/vad/`

| 模組名稱 | 文件 | 說明 | 主要參數 |
|---------|------|------|---------|
| WebRTC VAD | `webrtc.py` | 基於Google WebRTC的VAD實現 | `frame_size`, `aggressive_level` |
| Silero VAD | `silero.py` | 基於深度學習的預訓練VAD | `threshold`, `min_speech_duration_ms` |
| Adaptive VAD | `adaptive.py` | 可自適應閾值的VAD | `initial_threshold`, `adaptation_rate` |
| QA-VAD | `qa_vad.py` | 音頻質量感知VAD | `quality_threshold`, `base_vad` |

替換方法：在配置文件中修改 `vad.method` 和相應的 `vad.params`。

### 4.2 特徵提取模組
位置：`src/features/`

| 模組名稱 | 文件 | 說明 | 主要參數 |
|---------|------|------|---------|
| MFCC | `mfcc.py` | 梅爾頻率倒譜係數 | `n_mfcc`, `include_delta`, `include_delta_delta` |
| PLP | `plp.py` | 感知線性預測 | `n_plp`, `include_delta` |
| Pitch | `pitch.py` | 音高特徵提取 | `extract_jitter`, `extract_shimmer`, `extract_hnr` |

替換方法：在配置文件中修改 `features` 列表，可以使用多個特徵提取器。

### 4.3 對齊模組
位置：`src/alignment/`

| 模組名稱 | 文件 | 說明 | 主要參數 |
|---------|------|------|---------|
| MFA | `mfa.py` | Montreal Forced Aligner | `beam`, `retry_beam` |
| DTW | `dtw.py` | 動態時間規整 | `window_type`, `window_size` |

替換方法：在配置文件中修改 `alignment` 參數，支持單一對齊器或多對齊器。

### 4.4 評分模型
位置：`src/scoring/`

| 模組名稱 | 文件 | 說明 | 主要參數 |
|---------|------|------|---------|
| Random Forest | `rf_regressor.py` | 隨機森林回歸評分模型 | `n_estimators`, `max_depth`, `feature_selection` |

替換方法：在配置文件中修改 `scoring.method` 和 `scoring.params`。

## 5. 實驗配置詳解

實驗配置文件位於 `config/experiment_config.yaml`，主要包含以下部分：

### 5.1 全局參數
```yaml
global:
  sampling_rate: 16000        # 採樣率
  bit_depth: 16               # 位深度
  window_size: 0.025          # 分析窗長度（秒）
  hop_length: 0.010           # 分析窗步長（秒）
  preemphasis: 0.97           # 預加重係數
  data_path: "../data/raw"    # 原始數據路徑
  output_path: "../results"   # 結果保存路徑
  azure_results_path: "../data/azure_results"  # Azure結果路徑
  cross_validation_folds: 5   # 交叉驗證摺數
```

### 5.2 Stack配置
每個Stack定義一組實驗組件：
```yaml
stacks:
  stack1:
    name: "WebRTC+MFCC+MFA 基準實驗"
    description: "作為 baseline 對照"
    vad:
      method: "webrtc"
      params:
        frame_size: 30
        aggressive_level: 2
    features:
      - method: "mfcc"
        params:
          n_mfcc: 13
          include_delta: true
          include_delta_delta: true
    alignment:
      method: "mfa"
      params:
        beam: 10
        retry_beam: 40
    scoring:
      method: "rf_regressor"
      params:
        n_estimators: 100
        max_depth: 10
        min_samples_split: 5
```

### 5.3 評估指標配置
```yaml
evaluation:
  segmentation_metrics:
    - "rmse"
    - "dtw_distance"
    - "segment_length_bias"
    - "feature_retention_rate"
    - "silence_false_alarm_rate"
  scoring_metrics:
    - "pearson_correlation"
    - "spearman_correlation"
    - "mae"
    - "scoring_bias"
    - "r2"
    - "classification_consistency"
  
  visualization:
    - "scatter_plot"
    - "residual_plot"
    - "feature_importance"
    - "bland_altman_plot"
```

## 6. 數據集配置

數據集配置文件位於 `data/dataset_config.yaml`，主要包含以下部分：

```yaml
audio_dir: 'data/raw'                    # 音頻文件目錄
azure_results_path: 'data/azure_results' # Azure評分結果目錄
teacher_audio_dir: 'data/teacher'        # 教師音頻目錄
reference_segments_file: 'data/reference_segments.json' # 參考分段文件
include_patterns: ['*.wav']              # 要包含的音頻文件模式
exclude_patterns: ['*noise*.wav']        # 要排除的音頻文件模式
```

可以使用 `utils/data_utils.py` 中的 `create_dataset_config_template()` 函數建立模板：

```python
from utils.data_utils import create_dataset_config_template
create_dataset_config_template('path/to/my_dataset_config.yaml')
```

## 7. 工具函數說明

### 7.1 數據處理工具 (`utils/data_utils.py`)

| 函數名稱 | 說明 | 
|---------|------|
| `load_dataset()` | 加載數據集配置和音頻文件 |
| `prepare_features()` | 從特徵字典準備訓練數據 |
| `normalize_features()` | 特徵標準化 |
| `split_train_test()` | 分割訓練和測試集 |
| `create_dataset_config_template()` | 建立數據集配置模板 |
| `generate_batch()` | 生成訓練批次 |

### 7.2 可視化工具 (`utils/visualization.py`)

| 函數名稱 | 說明 |
|---------|------|
| `plot_scatter()` | 繪製系統分數與Azure分數散點圖 |
| `plot_residuals()` | 繪製殘差圖 |
| `plot_feature_importance()` | 繪製特徵重要性圖 |
| `plot_bland_altman()` | 繪製Bland-Altman一致性分析圖 |
| `plot_segmentation_comparison()` | 繪製VAD分割與參考分割比較圖 |
| `plot_metrics_comparison()` | 繪製不同Stack的指標比較圖 |
| `plot_correlation_matrix()` | 繪製特徵與目標的相關矩陣 |

## 8. 實驗流程步驟

典型的實驗流程包括以下步驟：

1. **準備數據**：將語音文件放入 `data/raw/`，將Azure評分結果放入 `data/azure_results/`
2. **配置實驗**：編輯或建立 `config/experiment_config.yaml`
3. **執行實驗**：運行 `python main.py`
4. **檢視結果**：結果保存在 `results/` 目錄中

### 實驗執行流程詳解

1. **數據加載**：加載音頻文件和Azure分數
2. **VAD處理**：使用選定的VAD模組檢測語音段
3. **特徵提取**：從語音段提取特徵
4. **對齊處理**：與教師音頻對齊
5. **評分模型訓練**：使用特徵訓練評分模型
6. **評估VAD和對齊**：計算分割評估指標
7. **評估評分效果**：計算與Azure分數的相關性
8. **生成可視化和報告**：生成圖表和摘要報告

## 9. 結果解釋

實驗結果將保存在 `results/{experiment_name}/` 目錄下，包括：

- **Stack結果目錄**：每個Stack有獨立的子目錄
  - `vad_segments/`：VAD分割結果
  - `features/`：提取的特徵
  - `alignments/`：對齊結果
  - `scoring/`：評分模型和預測結果
  - `visualizations/`：各種可視化圖表
- **摘要報告**：`experiment_summary.json`
- **比較表格**：`experiment_comparison.csv`

### 關鍵指標解釋

- **分割評估指標**：
  - `rmse`：VAD時間戳與參考時間戳的均方根誤差
  - `segment_length_bias`：切割段長偏差
  - `feature_retention_rate`：保留的有效特徵百分比
  
- **評分評估指標**：
  - `pearson_correlation`/`spearman_correlation`：與Azure分數的相關性
  - `mae`：平均絕對誤差
  - `r2`：決定係數
  - `scoring_bias`：系統傾向過高或過低的趨勢

## 10. 擴展開發指南

### 10.1 添加新的VAD方法

1. 在 `src/vad/` 目錄下創建新的Python模塊（如 `my_vad.py`）
2. 實現與其他VAD相同的接口（尤其是 `detect()` 和 `process_file()` 方法）
3. 在 `main.py` 中的 `ExperimentManager.__init__()` 方法中註冊新的VAD模塊：
   ```python
   self.vad_modules = {
       'webrtc': WebRTCVAD,
       'silero': SileroVAD,
       'my_vad': MyVAD  # 添加新的VAD
   }
   ```
4. 在配置文件中使用新的VAD方法：
   ```yaml
   vad:
     method: "my_vad"
     params:
       # 自定義參數
   ```

### 10.2 添加新的特徵提取方法

1. 在 `src/features/` 目錄下創建新的Python模塊
2. 實現與其他特徵提取器相同的接口（尤其是 `extract()` 和 `extract_from_segments()` 方法）
3. 在 `main.py` 中註冊新的特徵提取器
4. 在配置文件中使用新的特徵提取方法

### 10.3 整合深度學習方法

可以通過以下方式整合深度學習方法：

1. **基於TDNN的VAD**：在 `src/vad/` 下實現
2. **CNN-LSTM特徵提取**：在 `src/features/` 下實現
3. **深度學習評分模型**：在 `src/scoring/` 下實現，如添加基於深度學習的評分模型

## 11. 常見問題與故障排除

### 11.1 運行時錯誤

- **ImportError**：確保已安裝所有依賴，使用 `pip install -r requirements.txt`
- **FileNotFoundError**：檢查文件路徑是否正確，特別是數據和配置文件
- **RuntimeError: CUDA out of memory**：減少批次大小或使用CPU模式

### 11.2 配置問題

- **無法識別的VAD/特徵提取方法**：檢查拼寫，確保已在 `ExperimentManager` 中註冊
- **參數錯誤**：參考各組件文件中的參數說明

### 11.3 效能問題

- **評分模型效果不佳**：調整特徵提取參數或嘗試不同的評分模型
- **VAD切割不準確**：嘗試不同的VAD方法或調整參數

## 12. 單元測試框架

本專案包含一個完整的單元測試框架，使用 pytest 和 mock 來測試各個模組的功能。測試文件位於 `tests/` 目錄下。

### 12.1 運行測試

```bash
# 運行所有測試
cd project_experiment01
python -m pytest

# 運行特定模組的測試
python -m pytest tests/test_vad

# 生成測試覆蓋率報告
python -m pytest --cov=src
```

### 12.2 測試結構

測試目錄結構對應源代碼結構：

```
tests/
├── test_vad/              # VAD 模組測試
├── test_features/         # 特徵提取模組測試
└── test_alignment/        # 對齊模組測試
```

### 12.3 添加新測試

為新模組添加測試時，應遵循以下步驟：

1. 在對應的測試目錄中創建新的測試文件
2. 使用測試類和測試方法組織測試
3. 利用共享 fixtures 避免代碼重複
4. 使用 mock 隔離外部依賴

更多測試相關信息請參考 `tests/README.md`。 