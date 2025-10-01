# RPA自動專利比對機器人系統 - Azure AI Search與認知服務整合指南

本文將指導您完成Azure AI Search與認知服務的整合配置，建立強大的專利文件檢索與分析能力。這是實現RAG (檢索增強生成) 架構的關鍵步驟，將為您的RPA系統提供智能化的專利比對功能。

## 總覽

在這個階段，我們將配置以下核心組件：

1. **Azure AI Search索引** - 用於儲存和檢索專利文件
2. **認知技能集** - 提供文件處理、實體識別、關鍵詞提取等AI能力
3. **資料來源** - 連接到Azure Blob Storage中的專利文件
4. **索引器** - 自動化文件處理和索引更新流程
5. **Azure OpenAI模型** - 部署GPT-4、GPT-3.5和嵌入模型

### 系統架構

我們的RAG架構遵循以下流程：

```
專利文件 (PDF/Word) → Azure Blob Storage → AI Search索引器 → 認知技能集處理 → 結構化索引 → OpenAI嵌入 → 向量搜尋 → GPT模型生成回應
```

## 前置準備

在執行本階段的配置之前，請確保您已完成：

1. **Azure基礎設施準備** - 完成第一階段的基礎設施建置
2. **取得實際的資源名稱** - 記錄在第一階段建立的各項Azure資源的實際名稱
3. **準備測試文件** - 準備一些專利PDF文件用於測試索引功能

## 配置步驟

### 第一步：更新腳本中的資源名稱

開啟 `azure-config/scripts/setup_ai_search.sh` 和 `azure-config/scripts/deploy_openai_models.sh` 腳本，將以下變數替換為您在第一階段實際建立的資源名稱：

```bash
# 在 setup_ai_search.sh 中
SEARCH_SERVICE_NAME="your-actual-search-service-name"
STORAGE_ACCOUNT_NAME="your-actual-storage-account-name"
OPENAI_SERVICE_NAME="your-actual-openai-service-name"
KEY_VAULT_NAME="your-actual-keyvault-name"

# 在 deploy_openai_models.sh 中
OPENAI_SERVICE_NAME="your-actual-openai-service-name"
```

### 第二步：部署Azure OpenAI模型

首先部署必要的OpenAI模型。這些模型將用於文件分析、嵌入生成和智能回應。

```bash
./azure-config/scripts/deploy_openai_models.sh
```

此腳本將部署以下模型：

| 模型 | 用途 | 容量 (TPM) |
| :--- | :--- | :--- |
| **GPT-4** | 高品質的專利分析和報告生成 | 10,000 |
| **GPT-3.5 Turbo** | 快速的對話和簡單分析任務 | 30,000 |
| **text-embedding-ada-002** | 文件向量化和語義搜尋 | 30,000 |

> **注意**：模型部署可能需要5-10分鐘的時間。請耐心等候部署完成。

### 第三步：配置AI Search索引和技能集

執行AI Search配置腳本，建立完整的文件處理管線：

```bash
./azure-config/scripts/setup_ai_search.sh
```

此腳本將建立：

#### 1. 資料來源 (Data Source)
- 連接到Azure Blob Storage中的 `patent-documents` 容器
- 配置變更偵測，自動處理新增或修改的文件
- 支援軟刪除偵測

#### 2. 認知技能集 (Skillset)
包含以下AI處理技能：

| 技能 | 功能 | 支援語言 |
| :--- | :--- | :--- |
| **文件提取** | 從PDF、Word等格式提取文字和圖片 | 多語言 |
| **文字分割** | 將長文件分割成可管理的區塊 | 繁體中文 |
| **實體識別** | 識別人名、組織、地點、日期等實體 | 繁體中文 |
| **關鍵詞提取** | 提取重要的關鍵詞和詞組 | 繁體中文 |
| **OCR處理** | 從圖片中提取文字內容 | 繁體中文 |

#### 3. 搜尋索引 (Index)
建立包含以下欄位的結構化索引：

- **content** - 文件主要內容
- **pages** - 分頁內容陣列
- **keyPhrases** - 提取的關鍵詞
- **persons/organizations/locations** - 識別的實體
- **ocrText** - OCR提取的文字
- **metadata** - 檔案元資料

#### 4. 索引器 (Indexer)
- 自動化處理新文件
- 每2小時執行一次增量更新
- 支援批次處理和錯誤處理

### 第四步：上傳測試文件

將一些專利PDF文件上傳到Azure Blob Storage進行測試：

```bash
# 使用Azure CLI上傳文件
az storage blob upload \
    --account-name your-storage-account-name \
    --container-name patent-documents \
    --name "test-patent-1.pdf" \
    --file "/path/to/your/patent-file.pdf"
```

### 第五步：監控索引進度

使用以下命令監控索引器的執行狀態：

```bash
# 檢查索引器狀態
curl -H "api-key: YOUR_SEARCH_API_KEY" \
     "https://your-search-service.search.windows.net/indexers/patent-blob-indexer/status?api-version=2023-11-01"

# 檢查索引中的文件數量
curl -H "api-key: YOUR_SEARCH_API_KEY" \
     "https://your-search-service.search.windows.net/indexes/patent-documents/docs?api-version=2023-11-01&search=*&$count=true"
```

## 測試與驗證

### 基本搜尋測試

完成配置後，您可以測試搜尋功能：

```bash
# 基本關鍵字搜尋
curl -H "api-key: YOUR_SEARCH_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"search": "人工智慧", "top": 5}' \
     "https://your-search-service.search.windows.net/indexes/patent-documents/docs/search?api-version=2023-11-01"

# 語義搜尋 (需要Basic以上的SKU)
curl -H "api-key: YOUR_SEARCH_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"search": "機器學習演算法", "queryType": "semantic", "semanticConfiguration": "patent-semantic-config"}' \
     "https://your-search-service.search.windows.net/indexes/patent-documents/docs/search?api-version=2023-11-01"
```

### OpenAI API測試

測試OpenAI模型的連接：

```bash
# 測試GPT-3.5 Turbo
curl -H "Content-Type: application/json" \
     -H "api-key: YOUR_OPENAI_API_KEY" \
     -d '{"messages":[{"role":"user","content":"請簡述專利檢索的重要性"}],"max_tokens":200}' \
     "https://your-openai-service.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?api-version=2023-12-01-preview"

# 測試文字嵌入
curl -H "Content-Type: application/json" \
     -H "api-key: YOUR_OPENAI_API_KEY" \
     -d '{"input": "專利檢索系統"}' \
     "https://your-openai-service.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-12-01-preview"
```

## 效能調優建議

### 索引器最佳化

1. **批次大小調整** - 根據文件大小調整 `batchSize` 參數
2. **排程頻率** - 根據文件更新頻率調整索引器執行間隔
3. **技能集最佳化** - 根據實際需求啟用或停用特定的認知技能

### 搜尋效能最佳化

1. **欄位配置** - 僅對需要搜尋的欄位設定 `searchable: true`
2. **分析器選擇** - 使用適合的語言分析器提升搜尋品質
3. **快取策略** - 在應用程式層實施搜尋結果快取

## 成本最佳化

### AI Search成本控制

- **選擇適當的SKU** - 根據資料量和查詢頻率選擇合適的定價層
- **監控搜尋單位使用量** - 定期檢查副本和分割區的使用情況
- **最佳化索引大小** - 移除不必要的欄位以減少儲存成本

### OpenAI成本控制

- **模型選擇策略** - 對簡單任務使用GPT-3.5，複雜分析使用GPT-4
- **Token使用最佳化** - 實施適當的提示工程以減少Token消耗
- **快取機制** - 對常見查詢實施結果快取

## 疑難排解

### 常見問題

1. **索引器執行失敗**
   - 檢查Blob Storage的連接權限
   - 確認認知服務的配額和金鑰
   - 查看索引器的詳細錯誤訊息

2. **搜尋結果品質不佳**
   - 調整分析器設定
   - 檢查技能集的輸出對應
   - 考慮使用語義搜尋功能

3. **OpenAI API呼叫失敗**
   - 確認模型部署狀態
   - 檢查API金鑰和端點設定
   - 監控配額使用情況

## 下一步

完成AI Search與認知服務的整合後，您就可以進入下一個階段：**Azure部署與CI/CD配置**。在這個階段，我們將建立完整的容器化部署管線，並配置持續整合與持續部署流程。

---
*本文件由 Manus AI 自動生成。*
