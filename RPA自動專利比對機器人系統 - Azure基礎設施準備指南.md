# RPA自動專利比對機器人系統 - Azure基礎設施準備指南

本文將指導您完成在Microsoft Azure上部署「RPA自動專利比對機器人系統」所需的基礎設施準備工作。我們將使用Azure CLI腳本自動化大部分資源的建立過程，以確保一致性並減少手動錯誤。

## 總覽

此階段的目標是建立一個穩固、安全且可擴展的雲端基礎設施，以支援本系統的各個組件，包括後端API、前端應用、RPA機器人、資料庫、快取以及AI服務。

### 建立的資源

我們將透過自動化腳本建立以下Azure資源：

| 資源類型 | 用途 | SKU (範例) |
| :--- | :--- | :--- |
| **資源群組 (Resource Group)** | 集中管理所有相關資源 | N/A |
| **容器註冊表 (ACR)** | 儲存和管理Docker映像檔 | `Standard` |
| **Kubernetes服務 (AKS)** | 容器協調與管理 | `Standard_DS2_v2` (3節點) |
| **PostgreSQL資料庫** | 主要的結構化資料儲存 | `B_Gen5_2` |
| **Redis快取** | 快取常用資料以提升效能 | `Basic C0` (250MB) |
| **AI Search** | 提供強大的專利檢索與RAG能力 | `basic` |
| **OpenAI服務** | 提供大型語言模型能力 | `S0` |
| **Blob儲存體** | 儲存專利文件、報告等非結構化資料 | `Standard_LRS` |
| **Key Vault** | 安全地儲存和管理密鑰、密碼和憑證 | N/A |

## 前置準備

在執行腳本之前，請確保您已完成以下準備工作：

1.  **安裝 Azure CLI**：請參考 [Azure CLI 安裝指南](https://docs.microsoft.com/cli/azure/install-azure-cli) 完成安裝。
2.  **登入 Azure 帳戶**：開啟您的終端機或命令提示字元，執行 `az login` 並依照指示完成登入。
3.  **確認訂用帳戶**：如果您有多個Azure訂用帳戶，請使用 `az account set --subscription "<您的訂用帳戶名稱或ID>"` 設定要使用的訂用帳戶。
4.  **下載專案檔案**：確保您已取得完整的 `patent-rpa-system` 專案檔案，特別是 `azure-config/scripts/provision_azure_infra.sh` 腳本。

## 自動化部署步驟

我們強烈建議使用提供的Shell腳本來自動建立所有必要的Azure資源。這能確保所有資源都按照最佳實踐進行配置。

### 1. 檢視與修改腳本變數

開啟 `azure-config/scripts/provision_azure_infra.sh` 腳本。在檔案的開頭，您會看到一個配置變數區塊。請根據您的需求和命名慣例修改這些變數。

> **重要提示**：
> - `ACR_NAME`, `POSTGRES_SERVER_NAME`, `REDIS_CACHE_NAME`, `SEARCH_SERVICE_NAME`, `OPENAI_SERVICE_NAME`, `STORAGE_ACCOUNT_NAME`, `KEY_VAULT_NAME` 都必須是 **全域唯一** 的。腳本預設會附加隨機數，但您也可以自行指定。
> - **請務必修改 `POSTGRES_ADMIN_PASSWORD`** 為一個高強度的安全密碼。這非常重要！

```bash
# 資源群組
RESOURCE_GROUP="PatentRPASystemRG"
LOCATION="eastus" # 建議選擇離您最近的Azure區域

# ... 其他變數 ...

# Azure Database for PostgreSQL
POSTGRES_ADMIN_PASSWORD="your_secure_password_here_P@ssw0rd123!" # 請務必更換為高強度密碼

# ... 其他變數 ...
```

### 2. 賦予腳本執行權限

在終端機中，導覽至專案根目錄，並執行以下命令，賦予腳本執行權限：

```bash
chmod +x azure-config/scripts/provision_azure_infra.sh
```

### 3. 執行部署腳本

執行以下命令以開始建立Azure資源。整個過程可能需要 **15到30分鐘**，請耐心等候。

```bash
./azure-config/scripts/provision_azure_infra.sh
```

腳本會依序建立所有資源，並在過程中顯示進度。如果遇到任何錯誤，腳本會停止執行，您可以根據錯誤訊息進行排查。

### 4. 確認部署結果

腳本執行成功後，您會在終端機看到所有已建立資源的摘要資訊。您也可以登入 [Azure Portal](https://portal.azure.com/)，找到名為 `PatentRPASystemRG` 的資源群組，確認所有資源都已成功建立。

> **安全性最佳實踐**：
> 腳本會自動將所有重要的密鑰和連接字串（例如資料庫密碼、ACR密碼、儲存體連接字串等）儲存在新建立的 **Azure Key Vault** 中。在後續的應用程式部署階段，我們會配置應用程式從Key Vault中安全地讀取這些敏感資訊，而不是將它們硬編碼在設定檔中。

## 下一步

完成基礎設施的準備後，您就可以進入下一個階段：**Azure AI Search與認知服務整合**。在這個階段，我們將設定AI Search的索引、索引器，並與Blob儲存體和OpenAI服務進行整合，以實現強大的RPA知識管理與檢索能力。

---
*本文件由 Manus AI 自動生成。*




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




# RPA自動專利比對機器人系統 - Azure部署與CI/CD配置指南

本文將指導您完成系統的容器化部署以及建立完整的CI/CD管線。我們將使用Azure Kubernetes Service (AKS) 作為容器協調平台，並透過Azure DevOps建立自動化的持續整合與持續部署流程。

## 總覽

在這個階段，我們將完成以下關鍵任務：

1. **容器映像建置** - 將後端API、前端應用和RPA機器人打包成Docker映像
2. **Kubernetes部署配置** - 建立完整的K8s資源定義
3. **Azure DevOps CI/CD** - 設定自動化建置和部署管線
4. **監控與日誌** - 配置應用程式監控和日誌收集
5. **安全性配置** - 實施最佳安全實踐

### 部署架構

我們的部署架構採用微服務設計，包含以下組件：

```
Internet → Azure Load Balancer → AKS Ingress Controller → Services → Pods
                                                        ├── Frontend Pods (React)
                                                        ├── Backend Pods (FastAPI)
                                                        └── RPA Bots Pods (Python + Selenium)
```

## 前置準備

在開始部署之前，請確保您已完成：

1. **Azure基礎設施準備** - 完成第一階段的基礎設施建置
2. **AI Search配置** - 完成第二階段的AI服務整合
3. **Docker環境** - 確保本地或CI/CD環境有Docker
4. **kubectl工具** - 安裝Kubernetes命令列工具
5. **Azure DevOps專案** - 建立Azure DevOps專案（可選）

## 第一步：建置Docker映像

### 手動建置映像

如果您想要手動建置和推送映像到Azure Container Registry：

```bash
# 登入ACR
az acr login --name your-acr-name

# 建置後端映像
docker build -f docker/backend/Dockerfile -t your-acr-name.azurecr.io/patent-rpa-backend:latest .
docker push your-acr-name.azurecr.io/patent-rpa-backend:latest

# 建置前端映像
docker build -f docker/frontend/Dockerfile -t your-acr-name.azurecr.io/patent-rpa-frontend:latest .
docker push your-acr-name.azurecr.io/patent-rpa-frontend:latest

# 建置RPA機器人映像
docker build -f docker/rpa-bots/Dockerfile -t your-acr-name.azurecr.io/patent-rpa-bots:latest .
docker push your-acr-name.azurecr.io/patent-rpa-bots:latest
```

### 映像組成說明

| 映像 | 基礎映像 | 主要組件 | 用途 |
| :--- | :--- | :--- | :--- |
| **patent-rpa-backend** | `python:3.11-slim` | FastAPI, SQLAlchemy, Azure SDK | 提供REST API服務 |
| **patent-rpa-frontend** | `nginx:alpine` | React應用, Nginx | 提供Web使用者介面 |
| **patent-rpa-bots** | `python:3.11-slim` | Selenium, Chrome, RPA腳本 | 執行專利檢索機器人 |

## 第二步：配置Kubernetes資源

### 更新配置檔案

在部署之前，請更新以下配置檔案中的實際資源名稱：

#### 1. ConfigMap配置 (`azure-config/k8s/configmap.yaml`)

```yaml
# 更新以下值為您的實際資源名稱
POSTGRES_HOST: "your-actual-postgres-server.postgres.database.azure.com"
REDIS_HOST: "your-actual-redis-cache.redis.cache.windows.net"
AZURE_SEARCH_SERVICE_NAME: "your-actual-search-service"
# ... 其他配置
```

#### 2. Secret配置 (`azure-config/k8s/secret.yaml`)

```yaml
# 將敏感資訊進行base64編碼
# 例如：echo -n "your_password" | base64
POSTGRES_PASSWORD: "base64_encoded_password"
AZURE_OPENAI_API_KEY: "base64_encoded_api_key"
# ... 其他密鑰
```

#### 3. 部署配置

更新各個部署檔案中的映像名稱：

```yaml
# 在 backend-deployment.yaml, frontend-deployment.yaml, rpa-deployment.yaml 中
image: your-acr-name.azurecr.io/patent-rpa-backend:latest
```

### Kubernetes資源說明

我們的Kubernetes配置包含以下資源：

| 資源類型 | 名稱 | 用途 |
| :--- | :--- | :--- |
| **Namespace** | `patent-rpa-system` | 隔離應用程式資源 |
| **ConfigMap** | `patent-rpa-config` | 儲存非敏感配置 |
| **Secret** | `patent-rpa-secrets` | 儲存敏感資訊 |
| **Deployment** | `patent-rpa-backend` | 後端API服務 |
| **Deployment** | `patent-rpa-frontend` | 前端Web應用 |
| **Deployment** | `patent-rpa-bots` | RPA機器人服務 |
| **Service** | 各種服務 | 內部網路通訊 |
| **Ingress** | `patent-rpa-ingress` | 外部流量路由 |
| **HPA** | 自動擴展 | 根據負載自動調整Pod數量 |

## 第三步：執行部署

### 使用自動化腳本部署

我們提供了一個自動化部署腳本，可以簡化整個部署過程：

```bash
# 更新腳本中的資源名稱
vim azure-config/scripts/deploy_to_aks.sh

# 執行部署（使用latest標籤）
./azure-config/scripts/deploy_to_aks.sh

# 或指定特定的映像標籤
./azure-config/scripts/deploy_to_aks.sh v1.0.0
```

### 手動部署步驟

如果您偏好手動控制部署過程：

```bash
# 1. 連接到AKS叢集
az aks get-credentials --resource-group PatentRPASystemRG --name PatentRPACluster

# 2. 建立命名空間
kubectl apply -f azure-config/k8s/namespace.yaml

# 3. 建立ACR登入密鑰
kubectl create secret docker-registry acr-secret \
    --namespace=patent-rpa-system \
    --docker-server=your-acr.azurecr.io \
    --docker-username=your-acr-username \
    --docker-password=your-acr-password

# 4. 部署配置和密鑰
kubectl apply -f azure-config/k8s/configmap.yaml
kubectl apply -f azure-config/k8s/secret.yaml

# 5. 部署應用程式
kubectl apply -f azure-config/k8s/backend-deployment.yaml
kubectl apply -f azure-config/k8s/rpa-deployment.yaml
kubectl apply -f azure-config/k8s/frontend-deployment.yaml

# 6. 檢查部署狀態
kubectl get pods -n patent-rpa-system -w
```

## 第四步：設定Azure DevOps CI/CD

### 建立Azure DevOps專案

1. 登入 [Azure DevOps](https://dev.azure.com/)
2. 建立新專案：`Patent-RPA-System`
3. 匯入您的Git存儲庫

### 配置服務連接

在Azure DevOps中建立以下服務連接：

#### 1. Azure Resource Manager連接
- 名稱：`Azure-Service-Connection`
- 訂用帳戶：選擇您的Azure訂用帳戶
- 資源群組：`PatentRPASystemRG`

#### 2. Docker Registry連接
- 名稱：`ACR-Service-Connection`
- Registry URL：`https://your-acr.azurecr.io`
- 使用ACR的管理員認證

#### 3. Kubernetes連接
- 名稱：`AKS-Service-Connection`
- 叢集：選擇您的AKS叢集
- 命名空間：`patent-rpa-system`

### 配置管線變數

在Azure DevOps管線中設定以下變數：

| 變數名稱 | 值 | 是否加密 |
| :--- | :--- | :--- |
| `containerRegistry` | `your-acr.azurecr.io` | 否 |
| `resourceGroupName` | `PatentRPASystemRG` | 否 |
| `kubernetesCluster` | `PatentRPACluster` | 否 |
| `TeamsWebhookUrl` | Teams通知Webhook URL | 是 |

### 建立管線

1. 在Azure DevOps中選擇 **Pipelines** > **New pipeline**
2. 選擇您的程式碼存儲庫
3. 選擇 **Existing Azure Pipelines YAML file**
4. 選擇 `/azure-pipelines.yml`
5. 檢查並執行管線

### 管線功能說明

我們的CI/CD管線包含以下階段：

#### Build階段
- **程式碼檢出** - 取得最新程式碼
- **前端建置** - 使用pnpm建置React應用
- **後端測試** - 執行Python單元測試
- **Docker建置** - 建置並推送三個Docker映像
- **產物發布** - 發布Kubernetes配置檔案

#### Deploy階段
- **開發環境部署** - 當推送到`develop`分支時自動部署
- **生產環境部署** - 當推送到`main`分支時部署到生產環境
- **煙霧測試** - 部署後執行基本健康檢查

#### 通知階段
- **Teams通知** - 發送部署狀態到Microsoft Teams
- **狀態記錄** - 記錄部署詳細資訊

## 第五步：監控與維運

### 檢查部署狀態

```bash
# 檢查所有Pod狀態
kubectl get pods -n patent-rpa-system

# 檢查服務狀態
kubectl get services -n patent-rpa-system

# 檢查Ingress狀態
kubectl get ingress -n patent-rpa-system

# 查看Pod日誌
kubectl logs -f deployment/patent-rpa-backend -n patent-rpa-system
```

### 常用維運命令

```bash
# 重新啟動部署
kubectl rollout restart deployment/patent-rpa-backend -n patent-rpa-system

# 擴展Pod數量
kubectl scale deployment patent-rpa-backend --replicas=5 -n patent-rpa-system

# 進入Pod進行除錯
kubectl exec -it deployment/patent-rpa-backend -n patent-rpa-system -- /bin/bash

# 檢查資源使用情況
kubectl top pods -n patent-rpa-system
kubectl top nodes
```

### 健康檢查端點

我們的應用程式提供以下健康檢查端點：

| 服務 | 端點 | 用途 |
| :--- | :--- | :--- |
| **後端API** | `/health` | 檢查API服務狀態 |
| **RPA機器人** | `/health` | 檢查RPA服務狀態 |
| **前端** | `/` | 檢查Web應用可用性 |

## 安全性最佳實踐

### 1. 密鑰管理
- 使用Azure Key Vault儲存敏感資訊
- 在Kubernetes中使用Secret而非ConfigMap儲存密碼
- 定期輪換API金鑰和密碼

### 2. 網路安全
- 使用Kubernetes Network Policies限制Pod間通訊
- 配置Ingress SSL/TLS憑證
- 實施適當的CORS政策

### 3. 映像安全
- 定期掃描Docker映像的安全漏洞
- 使用最小化的基礎映像
- 不在映像中包含敏感資訊

### 4. 存取控制
- 使用Azure AD整合進行身份驗證
- 實施基於角色的存取控制 (RBAC)
- 限制對Kubernetes API的存取

## 效能最佳化

### 1. 資源配置
- 根據實際負載調整CPU和記憶體限制
- 使用HPA自動擴展Pod數量
- 配置適當的存活性和就緒性探針

### 2. 快取策略
- 使用Redis快取常用資料
- 實施HTTP快取標頭
- 配置CDN加速靜態資源

### 3. 資料庫最佳化
- 使用連接池管理資料庫連接
- 實施適當的索引策略
- 定期監控查詢效能

## 疑難排解

### 常見問題

#### 1. Pod無法啟動
```bash
# 檢查Pod事件
kubectl describe pod <pod-name> -n patent-rpa-system

# 檢查映像拉取問題
kubectl get events -n patent-rpa-system --sort-by=".lastTimestamp"
```

#### 2. 服務無法連接
```bash
# 檢查服務端點
kubectl get endpoints -n patent-rpa-system

# 測試服務連接
kubectl run test-pod --image=busybox -it --rm -- wget -qO- http://service-name
```

#### 3. Ingress無法存取
```bash
# 檢查Ingress控制器
kubectl get pods -n ingress-nginx

# 檢查Ingress規則
kubectl describe ingress patent-rpa-ingress -n patent-rpa-system
```

### 日誌收集

```bash
# 收集所有Pod日誌
kubectl logs -l app=patent-rpa-backend -n patent-rpa-system --tail=100

# 持續監控日誌
kubectl logs -f deployment/patent-rpa-backend -n patent-rpa-system
```

## 下一步

完成部署與CI/CD配置後，您可以進入下一個階段：**系統測試與監控設置**。在這個階段，我們將建立完整的監控儀表板、設定告警規則，並執行全面的系統測試。

---
*本文件由 Manus AI 自動生成。*




# RPA自動專利比對機器人系統 - 系統測試與監控設置指南

本文將指導您完成系統的全面測試以及建立完整的監控體系。我們將涵蓋功能測試、效能測試、負載測試，以及Azure監控服務的配置，確保系統在生產環境中的穩定運行。

## 總覽

在這個階段，我們將建立以下測試與監控機制：

1. **整合測試** - 驗證所有系統組件的正常運作
2. **負載測試** - 評估系統在高負載下的效能表現
3. **Azure監控配置** - 建立完整的監控和告警體系
4. **效能基準測試** - 建立系統效能基準線
5. **故障恢復測試** - 驗證系統的容錯能力

### 測試架構

我們的測試策略採用多層次方法：

```
單元測試 → 整合測試 → 系統測試 → 負載測試 → 使用者驗收測試
    ↓           ↓           ↓           ↓              ↓
  開發階段    CI/CD管線   部署驗證    效能評估      生產就緒
```

## 第一步：配置Azure監控服務

### 執行監控配置腳本

首先，我們需要建立完整的監控基礎設施：

```bash
# 更新腳本中的通知郵箱
vim azure-config/scripts/setup_monitoring.sh
# 修改 NOTIFICATION_EMAIL="admin@your-company.com"

# 執行監控配置
./azure-config/scripts/setup_monitoring.sh
```

此腳本將建立以下監控組件：

| 組件 | 用途 | 功能 |
| :--- | :--- | :--- |
| **Log Analytics Workspace** | 集中日誌收集與分析 | 儲存所有系統日誌 |
| **Application Insights** | 應用程式效能監控 | 追蹤API回應時間、錯誤率 |
| **Azure Monitor** | 基礎設施監控 | 監控CPU、記憶體、網路 |
| **Action Group** | 告警通知 | 發送郵件、Teams通知 |
| **Alert Rules** | 自動告警 | CPU、記憶體、Pod重啟告警 |

### 監控儀表板配置

腳本會自動建立一個自訂儀表板，包含以下關鍵指標：

#### 1. 基礎設施指標
- **AKS叢集CPU使用率** - 監控整體運算資源使用情況
- **記憶體使用率** - 追蹤記憶體消耗趨勢
- **網路流量** - 監控進出流量
- **磁碟I/O** - 追蹤儲存效能

#### 2. 應用程式指標
- **API回應時間** - 監控服務效能
- **錯誤率** - 追蹤系統穩定性
- **請求量** - 監控系統負載
- **可用性** - 追蹤服務正常運行時間

#### 3. 業務指標
- **專利檢索次數** - 監控核心功能使用情況
- **RPA機器人執行狀態** - 追蹤自動化流程
- **文件處理量** - 監控資料處理能力

## 第二步：執行整合測試

### 安裝測試依賴

```bash
# 安裝Python測試依賴
pip install pytest requests locust

# 或使用requirements檔案
echo "pytest>=7.0.0" >> tests/requirements.txt
echo "requests>=2.28.0" >> tests/requirements.txt
echo "locust>=2.14.0" >> tests/requirements.txt
pip install -r tests/requirements.txt
```

### 執行整合測試

我們提供了完整的整合測試腳本，可以驗證所有系統組件：

```bash
# 本地測試（如果系統在本地運行）
python tests/integration_tests.py --url http://localhost

# 生產環境測試
python tests/integration_tests.py --url https://patent-rpa.your-domain.com

# 儲存測試結果
python tests/integration_tests.py --url https://patent-rpa.your-domain.com --output test_results.json
```

### 整合測試涵蓋範圍

我們的整合測試包含以下測試項目：

| 測試類別 | 測試項目 | 驗證內容 |
| :--- | :--- | :--- |
| **健康檢查** | 前端、後端、RPA服務 | 所有服務正常回應 |
| **資料庫連接** | PostgreSQL、Redis | 資料庫連接正常 |
| **Azure服務** | AI Search、OpenAI | 外部服務整合正常 |
| **核心功能** | 專利檢索、RAG分析 | 業務邏輯正確執行 |
| **檔案處理** | 上傳、處理、儲存 | 檔案操作流程正常 |
| **效能指標** | 回應時間、吞吐量 | 效能符合預期 |

### 測試結果解讀

測試腳本會產生詳細的測試報告：

```json
{
  "timestamp": "2024-01-15 10:30:00",
  "health_checks": {
    "frontend": true,
    "backend": true,
    "rpa": true
  },
  "database_connection": true,
  "redis_connection": true,
  "azure_ai_search": true,
  "openai_connection": true,
  "patent_search_api": true,
  "rpa_robot_status": {
    "twpat-searcher": true,
    "uspto-searcher": true,
    "multi-db-searcher": true
  },
  "file_upload": true,
  "rag_analysis": true,
  "performance_metrics": {
    "api_response_time": 0.15,
    "search_response_time": 2.3
  },
  "summary": {
    "total_tests": 15,
    "passed_tests": 15,
    "pass_rate": 100.0
  }
}
```

## 第三步：執行負載測試

### 使用Locust進行負載測試

我們提供了專業的負載測試腳本，模擬真實使用者行為：

```bash
# 安裝Locust
pip install locust

# 執行負載測試（Web介面）
locust -f tests/load_tests.py --host=https://patent-rpa.your-domain.com

# 命令列模式執行
locust -f tests/load_tests.py --host=https://patent-rpa.your-domain.com \
       --users 100 --spawn-rate 10 --run-time 300s --headless
```

### 負載測試場景

我們的負載測試模擬三種使用者類型：

#### 1. 一般使用者 (PatentRPAUser)
- **操作頻率**: 1-3秒間隔
- **主要操作**: 健康檢查、專利檢索、RAG分析
- **權重**: 標準

#### 2. 管理員使用者 (AdminUser)
- **操作頻率**: 5-10秒間隔
- **主要操作**: 系統狀態檢查、分析報告查看
- **權重**: 低

#### 3. 重度使用者 (HeavyUser)
- **操作頻率**: 0.5-1.5秒間隔
- **主要操作**: 密集搜尋、批次分析
- **權重**: 高

### 效能基準線

根據我們的測試，系統應達到以下效能指標：

| 指標 | 目標值 | 可接受範圍 |
| :--- | :--- | :--- |
| **API回應時間** | < 200ms | < 500ms |
| **專利檢索回應時間** | < 3秒 | < 5秒 |
| **RAG分析回應時間** | < 10秒 | < 15秒 |
| **併發使用者數** | 100+ | 50+ |
| **系統可用性** | 99.9% | 99.5% |
| **錯誤率** | < 0.1% | < 1% |

## 第四步：監控告警配置

### 關鍵告警規則

我們的監控腳本會自動建立以下告警規則：

#### 1. 資源使用告警
```bash
# CPU使用率超過80%
CPU使用率 > 80% (持續5分鐘)

# 記憶體使用率超過85%
記憶體使用率 > 85% (持續5分鐘)

# 磁碟使用率超過90%
磁碟使用率 > 90% (持續10分鐘)
```

#### 2. 應用程式告警
```bash
# API錯誤率過高
錯誤率 > 5% (持續3分鐘)

# 回應時間過長
平均回應時間 > 5秒 (持續5分鐘)

# Pod重啟次數過多
Pod重啟次數 > 5次 (15分鐘內)
```

#### 3. 業務邏輯告警
```bash
# RPA機器人執行失敗
機器人失敗率 > 10% (持續10分鐘)

# 專利檢索服務異常
檢索成功率 < 95% (持續5分鐘)
```

### 自訂Log Analytics查詢

我們提供了常用的KQL查詢，用於深入分析系統狀態：

```kusto
// 查詢1: 檢視所有Pod的狀態
KubePodInventory
| where Namespace == "patent-rpa-system"
| summarize arg_max(TimeGenerated, *) by Name
| project TimeGenerated, Name, PodStatus, ContainerRestartCount, Node

// 查詢2: 檢視應用程式錯誤日誌
ContainerLog
| where LogEntry contains "ERROR" or LogEntry contains "Exception"
| where Name contains "patent-rpa"
| project TimeGenerated, Name, LogEntry
| order by TimeGenerated desc
| take 100

// 查詢3: 監控API回應時間
requests
| where name contains "api"
| summarize avg(duration), count() by bin(timestamp, 5m), name
| order by timestamp desc
```

## 第五步：故障恢復測試

### Chaos Engineering測試

為了驗證系統的容錯能力，我們建議執行以下故障模擬測試：

#### 1. Pod故障測試
```bash
# 隨機刪除Pod測試自動恢復
kubectl delete pod -l app=patent-rpa-backend -n patent-rpa-system --random

# 觀察Pod重新啟動
kubectl get pods -n patent-rpa-system -w
```

#### 2. 網路故障測試
```bash
# 模擬網路延遲
kubectl exec -it deployment/patent-rpa-backend -n patent-rpa-system -- \
  tc qdisc add dev eth0 root netem delay 100ms

# 恢復網路
kubectl exec -it deployment/patent-rpa-backend -n patent-rpa-system -- \
  tc qdisc del dev eth0 root
```

#### 3. 資源限制測試
```bash
# 增加CPU負載測試
kubectl exec -it deployment/patent-rpa-backend -n patent-rpa-system -- \
  stress --cpu 4 --timeout 60s

# 增加記憶體負載測試
kubectl exec -it deployment/patent-rpa-backend -n patent-rpa-system -- \
  stress --vm 2 --vm-bytes 512M --timeout 60s
```

## 第六步：持續監控最佳實踐

### 1. 日誌管理
- **結構化日誌** - 使用JSON格式記錄關鍵事件
- **日誌等級** - 適當設定DEBUG、INFO、WARN、ERROR等級
- **日誌輪轉** - 定期清理舊日誌避免磁碟空間不足
- **敏感資訊** - 避免在日誌中記錄密碼、API金鑰等敏感資訊

### 2. 指標收集
- **業務指標** - 追蹤專利檢索次數、使用者活躍度
- **技術指標** - 監控回應時間、錯誤率、吞吐量
- **基礎設施指標** - 追蹤CPU、記憶體、網路、磁碟使用情況

### 3. 告警策略
- **分級告警** - 區分緊急、重要、一般等級
- **告警抑制** - 避免告警風暴，設定適當的抑制規則
- **升級機制** - 建立告警升級流程，確保重要問題得到及時處理

### 4. 效能最佳化
- **定期檢視** - 每週檢視效能指標趨勢
- **容量規劃** - 根據使用量增長預測資源需求
- **瓶頸識別** - 主動識別和解決效能瓶頸

## 疑難排解指南

### 常見問題診斷

#### 1. 服務無法啟動
```bash
# 檢查Pod狀態
kubectl describe pod <pod-name> -n patent-rpa-system

# 檢查事件日誌
kubectl get events -n patent-rpa-system --sort-by=".lastTimestamp"

# 檢查容器日誌
kubectl logs <pod-name> -n patent-rpa-system -c <container-name>
```

#### 2. 效能問題診斷
```bash
# 檢查資源使用情況
kubectl top pods -n patent-rpa-system
kubectl top nodes

# 檢查網路連接
kubectl exec -it <pod-name> -n patent-rpa-system -- netstat -tuln

# 檢查磁碟使用情況
kubectl exec -it <pod-name> -n patent-rpa-system -- df -h
```

#### 3. 資料庫連接問題
```bash
# 測試資料庫連接
kubectl exec -it deployment/patent-rpa-backend -n patent-rpa-system -- \
  python -c "import psycopg2; print(\'Database connection test\')"

# 檢查Redis連接
kubectl exec -it deployment/patent-rpa-backend -n patent-rpa-system -- \
  redis-cli -h redis-host ping
```

### 效能調優建議

#### 1. 應用程式層面
- **連接池最佳化** - 調整資料庫連接池大小
- **快取策略** - 實施適當的快取機制
- **非同步處理** - 使用非同步處理提升併發能力

#### 2. 基礎設施層面
- **資源配置** - 根據實際負載調整CPU和記憶體限制
- **自動擴展** - 配置HPA和VPA自動調整資源
- **網路最佳化** - 使用適當的網路政策和服務網格

## 下一步

完成系統測試與監控設置後，您可以進入最後一個階段：**完整部署指南文件撰寫**。在這個階段，我們將整合所有前面的步驟，撰寫一份完整的部署手冊，讓其他團隊成員也能順利部署和維護這個系統。

---
*本文件由 Manus AI 自動生成。*

