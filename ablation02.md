# 🔬 ablation03.md：Full Factorial 實驗設計（共 32 組）

本文件整理所有 VAD × 特徵提取 × 對齊策略 的全交叉組合，用以分析各模組與其交互作用對語音評分系統效能的影響。

---

## 🎯 實驗目的

本實驗旨在補足單變項消融的限制，透過完整交叉（Full Factorial Design）：
- 系統性測試模組間的交互效果（e.g., VAD × 特徵）
- 評估最穩定、泛化性最強的組合模組
- 尋找組合中是否存在非線性相乘提升（synergistic effect）

---

## ⚙️ 組合來源

| 模組類型     | 可選項                         |
|--------------|---------------------------------|
| VAD 方法     | WebRTC, Silero, Adaptive, QA-VAD |
| 特徵提取     | MFCC, MFCC+PLP, MFCC+Pitch, MFCC+PLP+Pitch |
| 對齊方式     | MFA, MFA+DTW                    |

**總組合數量 = 4 × 4 × 2 = ✅ 32 組**

---

## 📁 實驗命名規則

- 每組組合以 `F01 ~ F32` 編號
- 存放於 `experiments/f01/`、`experiments/f02/` … 依此類推
- 每個實驗皆使用相同語音資料、相同系統評分模型（Random Forest）

---

## 📊 實驗欄位說明

| ID   | VAD      | Features             | Alignment  | Purpose                    |
|------|----------|----------------------|------------|----------------------------|
| F01  | WebRTC   | MFCC                 | MFA        | Full Factorial Combination |
| F02  | WebRTC   | MFCC                 | MFA+DTW    | Full Factorial Combination |
| F03  | WebRTC   | MFCC+PLP             | MFA        | Full Factorial Combination |
| F04  | WebRTC   | MFCC+PLP             | MFA+DTW    | Full Factorial Combination |
| ...  | ...      | ...                  | ...        | ...                        |
| F31  | QA-VAD   | MFCC+PLP+Pitch       | MFA        | Full Factorial Combination |
| F32  | QA-VAD   | MFCC+PLP+Pitch       | MFA+DTW    | Full Factorial Combination |

共計 32 組（詳見實驗表格）

---

## ✅ 建議分析方法

1. 比較每一個模組在固定其他變項下的效能差異
2. 計算模組平均貢獻（e.g., Silero 平均表現優於其他 VAD 嗎？）
3. 使用 ANOVA / 回歸分析檢查交互項影響（若進行統計推論）
4. 製作模組貢獻熱力圖，或以主成分方式視覺化組合分佈

---

## 📌 注意事項

- 若時間或資源有限，可優先執行：
  - 每個 VAD 對應一個特徵組合（固定對齊）
  - 每個特徵對應一個 VAD（固定對齊）
  - 最後選定最佳 VAD+特徵，比較 MFA vs MFA+DTW

---

## 🧠 可擴展設計

- 將每組組合執行多次（n=3）以計算穩定性
- 加入系統評分與 Azure 評分之相關性（r 值、MAE）
- 將結果統整為一張 32 組比較大表（包含各指標）

---

