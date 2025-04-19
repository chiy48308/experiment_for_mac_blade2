# 語音評分實驗框架

## 專案概述

本專案實現了一個模組化的語音評分實驗框架，用於評估不同語音活動偵測（VAD）方法與特徵提取策略對整體語音切割準確性與自動發音評分系統效能之影響。

本研究採用 Stack 式模組化架構，進行消融實驗（Ablation Study），逐步移除或替換 VAD 方法、特徵提取方式與品質篩選機制，以觀察各模組對語音評分結果的影響，並以 Azure API 作為外部驗證依據，驗證系統穩定性與效度

## 目錄結構

```
project_experiment01/
├── data/                    # 語音資料集
│   ├── raw/                 # 原始語音檔
│   ├── processed/           # 預處理後的資料
│   └── azure_results/       # Azure API 回傳結果
├── src/                     # 源碼
│   ├── vad/                 # 語音活動偵測模組
│   │   ├── webrtc.py        # WebRTC VAD實現
│   │   ├── silero.py        # Silero VAD實現
│   │   ├── adaptive.py      # 自適應閾值VAD實現
│   │   └── qa_vad.py        # 品質感知VAD實現
│   ├── features/            # 特徵提取模組
│   │   ├── mfcc.py          # MFCC特徵提取
│   │   ├── plp.py           # PLP特徵提取
│   │   └── pitch.py         # 音高特徵提取
│   ├── alignment/           # 對齊模組
│   │   ├── mfa.py           # Montreal Forced Aligner實現
│   │   └── dtw.py           # 動態時間規整實現
│   ├── scoring/             # 評分模組
│   │   └── rf_regressor.py  # 隨機森林回歸模型
│   ├── evaluation/          # 評估指標計算
│   │   ├── segmentation_metrics.py  # 分割評估指標
│   │   └── scoring_metrics.py       # 評分評估指標
│   └── azure/               # Azure API 整合
│       └── speech_scoring.py        # Azure語音評分服務
├── experiments/             # 實驗配置
│   ├── stack1/              # Stack 1實驗結果
│   ├── stack2/              # Stack 2實驗結果
│   ├── stack3/              # Stack 3實驗結果
│   ├── stack4/              # Stack 4實驗結果
│   └── stack5/              # Stack 5實驗結果
├── results/                 # 實驗結果
│   ├── metrics/             # 評估指標結果
│   ├── features/            # 特徵文件
│   ├── alignments/          # 對齊結果
│   └── visualizations/      # 可視化圖表
├── notebooks/               # 分析和可視化筆記本
├── config/                  # 配置文件
│   ├── data_config.yaml     # 資料配置
│   ├── model_config.yaml    # 模型參數配置
│   └── experiment_config.yaml # 實驗配置
├── main.py                  # 主執行程式
└── utils/                   # 工具函數
    ├── data_utils.py        # 資料處理工具
    └── visualization.py     # 可視化工具
```

## 實驗 Stack 描述

本專案實現了5個不同的實驗組合（Stack）：

1. **Stack #1: WebRTC + MFCC + MFA + RFRegressor**
   - 基準實驗組，使用WebRTC進行VAD，MFCC特徵，MFA對齊，隨機森林評分

2. **Stack #2: Silero + MFCC + MFA + RFRegressor**
   - 使用預訓練的Silero VAD模型改善切割精度

3. **Stack #3: Adaptive VAD + MFCC+PLP + MFA+DTW + RFRegressor**
   - 使用自適應閾值VAD，融合MFCC和PLP特徵，結合MFA和DTW對齊

4. **Stack #4: QA-VAD + MFCC+pitch + MFA+DTW + RFRegressor**
   - 引入品質感知VAD，融合MFCC和音高特徵

5. **Stack #5: 無VAD + MFA（理論基準組）**
   - 沒有VAD的對照組，直接使用MFA進行對齊

## 安裝與環境配置

### 環境需求

- Python 3.8+
- Libraries: numpy, pandas, scikit-learn, librosa, webrtcvad, PyYAML

### 安裝依賴

```bash
pip install -r requirements.txt
```

## 使用方法

### 準備資料

1. 將語音檔案放入 `data/raw/` 目錄
2. 將Azure評分結果放入 `data/azure_results/` 目錄
3. 配置 `data/dataset_config.yaml` 文件，指定音檔路徑和對應的Azure分數

### 配置實驗

編輯 `config/experiment_config.yaml` 文件，設定各個Stack的參數

### 運行實驗

運行全部Stack:
```bash
python main.py
```

運行特定Stack:
```bash
python main.py -s stack1
```

指定實驗名稱:
```bash
python main.py -n my_experiment
```

### 查看結果

- 實驗結果將保存在 `results/[experiment_name]/` 目錄下
- 每個Stack的結果都有獨立的子目錄
- 總結報表保存在 `results/[experiment_name]/experiment_summary.json`
- 比較表格保存在 `results/[experiment_name]/experiment_comparison.csv`

## 擴展開發

### 添加新的VAD方法

1. 在 `src/vad/` 目錄下創建新的Python模塊
2. 實現與其他VAD相同的接口
3. 在 `main.py` 中註冊新的VAD模塊
4. 在配置文件中使用新的VAD方法

### 添加新的特徵提取方法

1. 在 `src/features/` 目錄下創建新的Python模塊
2. 實現特徵提取接口
3. 在 `main.py` 中註冊新的特徵提取器
4. 在配置文件中使用新的特徵提取方法

### 整合深度學習方法

可以通過以下方式整合深度學習方法:

1. 在 `src/vad/` 下添加基於深度學習的VAD實現（例如TDNN）
2. 在 `src/features/` 下添加基於CNN-LSTM的特徵提取器
3. 在 `src/scoring/` 下添加深度學習評分模型

## 引用與參考

- WebRTC VAD: https://github.com/wiseman/py-webrtcvad
- Silero VAD: https://github.com/snakers4/silero-vad
- Montreal Forced Aligner: https://montreal-forced-aligner.readthedocs.io/

## 許可證

MIT 