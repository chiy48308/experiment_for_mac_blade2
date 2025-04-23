# Git 管理策略指南

## 專案結構概述

本專案採用主倉庫 + 子專案的結構，各子專案彼此獨立且具有版本關係。例如：

```
experiment_for_mac_blade2/ (主倉庫)
├── project_experiment01/
├── project_experiment02/
├── project_experiment03/
└── ...
```

## Git 子模組管理策略

由於子專案間彼此獨立並具有各自的版本演進，我們採用 Git 子模組（Submodule）管理方式。

### 初始設置子模組

1. **添加新子模組**
   ```bash
   git submodule add <子模組倉庫URL> <本地子模組路徑>
   # 例如：
   git submodule add https://github.com/user/project_experiment04.git project_experiment04
   ```

2. **提交子模組信息**
   ```bash
   git commit -m "添加子模組 project_experimentXX"
   ```

### 克隆包含子模組的專案

1. **克隆主倉庫並初始化所有子模組**
   ```bash
   git clone --recursive <主倉庫URL>
   ```

2. **如果已經克隆了主倉庫但沒有子模組內容**
   ```bash
   git submodule init
   git submodule update
   ```

## 日常開發工作流程

### 更新子模組

1. **拉取最新子模組變更**
   ```bash
   # 更新所有子模組到遠程跟蹤分支的最新提交
   git submodule update --remote

   # 或者更新特定子模組
   git submodule update --remote project_experimentXX
   ```

2. **在子模組中工作**
   ```bash
   # 進入子模組目錄
   cd project_experimentXX

   # 在子模組中工作，進行編輯、提交等
   git checkout main  # 或者其他分支
   # ... 進行更改 ...
   git add .
   git commit -m "更改描述"
   git push

   # 返回主倉庫
   cd ..
   ```

3. **提交對子模組引用的更改**
   ```bash
   # 主倉庫現在會顯示子模組有更改，需要提交這些更改
   git add project_experimentXX
   git commit -m "更新子模組 project_experimentXX 到新版本"
   git push
   ```

### 固定子模組版本

如果需要將子模組鎖定到特定版本：

```bash
cd project_experimentXX
git checkout <特定提交SHA或標籤>
cd ..
git add project_experimentXX
git commit -m "將子模組 project_experimentXX 固定到版本 vX.Y.Z"
```

## 版本發布流程

1. **為主倉庫創建發布標籤**
   ```bash
   git tag -a v1.0.0 -m "版本 1.0.0 發布"
   git push origin v1.0.0
   ```

2. **為子模組創建發布標籤**
   ```bash
   cd project_experimentXX
   git tag -a v1.2.0 -m "子模組 project_experimentXX 版本 1.2.0"
   git push origin v1.2.0
   cd ..
   ```

3. **在發布文檔中記錄子模組版本**
   
   在發布說明中記錄所使用的子模組版本信息：
   ```
   發布版本：v1.0.0
   使用的子模組版本：
   - project_experiment01: v2.3.1
   - project_experiment02: v1.5.0
   - project_experiment03: v3.0.2
   ```

## 子模組轉換與修復

### 將普通目錄轉換為子模組

如果已有的目錄需要轉換為子模組：

1. **移動現有文件**
   ```bash
   # 備份現有文件
   mv project_experimentXX project_experimentXX_backup
   
   # 添加子模組
   git submodule add <子模組倉庫URL> project_experimentXX
   
   # 複製文件到新子模組
   cp -r project_experimentXX_backup/* project_experimentXX/
   
   # 在子模組中提交文件
   cd project_experimentXX
   git add .
   git commit -m "初始導入文件"
   git push
   cd ..
   
   # 提交子模組引用
   git add project_experimentXX
   git commit -m "將 project_experimentXX 轉換為子模組"
   ```

### 子模組問題修復

如果子模組狀態異常：

1. **子模組內容丟失**
   ```bash
   git submodule update --init --recursive
   ```

2. **子模組引用錯誤**
   ```bash
   # 刪除問題子模組的註冊
   git submodule deinit -f project_experimentXX
   git rm -f project_experimentXX
   rm -rf .git/modules/project_experimentXX
   
   # 重新添加子模組
   git submodule add <子模組倉庫URL> project_experimentXX
   ```

## 最佳實踐與注意事項

1. **子模組提交規範**
   - 子模組內的所有更改都應該先在子模組倉庫中提交並推送
   - 然後再在主倉庫中提交對子模組引用的更新

2. **避免分離頭指針狀態**
   - 在子模組中工作前，總是先切換到特定分支
   - 例如：`cd project_experimentXX && git checkout main`

3. **文檔化子模組依賴**
   - 在 README.md 中清晰記錄專案包含哪些子模組
   - 說明克隆和更新子模組的正確步驟

4. **定期更新子模組引用**
   - 避免子模組引用過時，導致整合困難

5. **權限管理**
   - 確保團隊成員對主倉庫和各子模組都有適當的訪問權限

6. **子模組測試**
   - 為每個子模組維護獨立的測試套件
   - 在更新子模組引用前先確保其通過測試

## 常見問題解決

1. **子模組顯示 "HEAD 分離於..."**
   
   這是正常情況，子模組預設指向特定提交而非分支。若要在子模組中工作，先切換到特定分支：
   ```bash
   cd project_experimentXX
   git checkout main  # 或其他分支
   ```

2. **子模組更改未被主倉庫檢測到**
   
   確保在子模組中提交並推送更改後，回到主倉庫提交對子模組引用的更新。

3. **克隆時子模組目錄為空**
   
   使用 `git clone --recursive` 或手動執行：
   ```bash
   git submodule init
   git submodule update
   ```

---

透過遵循以上指南，您可以有效管理多個獨立但具有版本關聯的子專案，保持代碼庫的整潔與可維護性。 