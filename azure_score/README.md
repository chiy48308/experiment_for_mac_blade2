# Azure 語音服務發音評估

這是一個使用 Azure 語音服務進行英語發音評估的工具。此工具可以分析語音，並提供發音準確度、流暢度、完整度和韻律等方面的評分，適合用於語言學習和教學研究。

## 功能特點

- 發音準確度評估（單詞和音素級別）
- 語音流暢度評分
- 完整度評估
- 韻律評估（語調、節奏等）
- 詳細的評分報告（JSON格式）

## 設置步驟

1. 確保已安裝 Python 3.6 或更高版本
2. 安裝所需的依賴：

```bash
# 激活虛擬環境
source venv/bin/activate

# 安裝 Azure 語音服務 SDK
pip install azure-cognitiveservices-speech
```

3. 設置 Azure 語音服務：
   - 在 [Azure 門戶](https://portal.azure.com/) 建立一個語音服務資源
   - 獲取語音服務的訂閱金鑰和區域
   - 設置環境變數：

```bash
# 在 macOS/Linux 上
export SPEECH_KEY=your_speech_key
export SPEECH_REGION=your_speech_region

# 在 Windows 上
set SPEECH_KEY=your_speech_key
set SPEECH_REGION=your_speech_region
```

## 使用方法

1. 準備一個音頻文件（WAV 格式推薦）
2. 運行腳本：

```bash
python pronunciation_assessment.py
```

3. 按提示輸入音頻文件路徑和參考文本
4. 查看評估結果

## 評估結果說明

- **發音準確度**：評估發音的正確性 (0-100)
- **流暢度**：評估語句間的停頓和連貫性 (0-100)
- **完整度**：評估相對於參考文本讀出的單詞比例 (0-100)
- **發音總分**：綜合以上各項的總體評分 (0-100)
- **詳細結果**：包含單詞級和音素級的詳細評分

## 支持的語言

這個工具支持多種語言的發音評估，包括：
- 英語（美式、英式、澳式）
- 中文
- 法語
- 德語
- 西班牙語
- 日語

請注意，韻律評估功能目前僅支持美式英語。

## 注意事項

- 需要穩定的網絡連接
- 音頻文件應有良好的音質
- 語音服務會產生使用費用，請查閱 [Azure 定價](https://azure.microsoft.com/zh-tw/pricing/details/cognitive-services/speech-services/)

## 常見問題

**問**：為什麼我的評估結果顯示錯誤？  
**答**：請確認環境變數已正確設置，並且音頻文件格式正確。

**問**：如何改進評分結果？  
**答**：嘗試在安靜的環境中錄音，確保麥克風質量良好，並清晰、自然地發音。

## 相關論文

- Chen, W. et al. (2021). A Comparative Study of Automated English Pronunciation Assessment Tools. 