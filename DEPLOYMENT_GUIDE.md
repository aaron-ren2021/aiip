# RPA自動專利比對機器人系統 - 部署指南

## 概述

本指南將協助您完成RPA自動專利比對機器人系統的完整部署，包含程式碼檢查、錯誤修復、和Azure Kubernetes Service (AKS) 部署。

## 已完成的程式碼審查和修復

### 🔧 結構性改進

1. **模組化架構**
   - 建立了正確的 `models/`, `services/`, `utils/` 目錄結構
   - 新增 `__init__.py` 檔案建立Python套件
   - 修正所有import路徑問題

2. **Pydantic v2 相容性**
   - 將 `@validator` 更新為 `@field_validator`
   - 修正驗證器函數簽章以符合Pydantic v2 API

3. **資料庫連線修復**
   - 修正資料庫管理器singleton實例化
   - 新增全域 `db_manager` 變數
   - 提供便利函數 `init_db()` 和 `get_db_session()`

### 🐛 錯誤處理改進

1. **啟動錯誤處理**
   - 改進 `main.py` 中的啟動錯誤處理
   - 避免啟動失敗導致整個系統崩潰
   - 在健康檢查中反映初始化問題

2. **import錯誤修復**
   - 修正 `multi_db_coordinator.py` 中的import路徑
   - 確保所有模組都能正確導入

### 📦 容器化改進

1. **Dockerfile 優化**
   - 更新以匹配當前專案結構
   - 新增Chromium和WebDriver支援RPA功能
   - 新增必要的系統目錄建立

2. **依賴項更新**
   - 新增 Selenium, BeautifulSoup4, webdriver-manager
   - 更新 requirements.txt 以包含所有必要套件

3. **資料庫初始化**
   - 建立 `sql/init.sql` 初始化腳本
   - 定義完整的資料表結構和索引
   - 修正 docker-compose.yml 中的SQL路徑

### 🚀 部署工具

1. **驗證腳本** (`validate_deployment.py`)
   - 檢查Python版本
   - 驗證必要檔案存在
   - 檢查環境變數配置
   - 測試Python依賴項導入
   - 進行語法錯誤檢查

2. **增強部署腳本** (`deploy_with_validation.sh`)
   - 包含完整的前置檢查
   - 彩色輸出和詳細日誌
   - 自動Azure登入檢查
   - ACR憑證設定
   - 按順序部署Kubernetes資源
   - 部署狀態監控

3. **監控腳本** (`monitor_deployment.py`)
   - 即時Pod狀態監控
   - Deployment就緒狀態檢查
   - Service配置檢視
   - API健康檢查
   - 日誌檢視功能
   - 持續監控模式

## 部署步驟

### 前提條件

確保您已安裝以下工具：
- Docker
- kubectl
- Azure CLI
- Python 3.8+

### 1. 驗證系統狀態

```bash
# 執行部署前檢查
python3 validate_deployment.py
```

### 2. 設定環境變數

建立 `.env` 檔案或設定環境變數：

```bash
export POSTGRES_HOST="your-postgres-host"
export POSTGRES_USER="patent_admin"
export POSTGRES_PASSWORD="your-secure-password"
export AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/"
export AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
export AZURE_SEARCH_KEY="your-search-key"
export AZURE_OPENAI_API_KEY="your-openai-key"
```

### 3. 執行部署

使用增強版部署腳本：

```bash
# 部署最新版本
./deploy_with_validation.sh

# 部署特定版本
./deploy_with_validation.sh v1.2.3
```

### 4. 監控部署狀態

```bash
# 一次性狀態檢查
python3 monitor_deployment.py

# 持續監控模式
python3 monitor_deployment.py --continuous

# 檢視特定組件日誌
python3 monitor_deployment.py --logs patent-rpa-backend
```

## 本地開發部署

使用Docker Compose進行本地開發：

```bash
# 啟動所有服務
docker-compose up -d

# 檢視服務狀態
docker-compose ps

# 檢視日誌
docker-compose logs -f backend

# 停止所有服務
docker-compose down
```

## 故障排除

### 常見問題

1. **依賴項安裝失敗**
   ```bash
   # 更新pip並重新安裝
   pip3 install --upgrade pip
   pip3 install -r requirements.txt
   ```

2. **Azure登入問題**
   ```bash
   # 重新登入Azure
   az logout
   az login
   ```

3. **Kubernetes連線問題**
   ```bash
   # 重新取得AKS憑證
   az aks get-credentials --resource-group PatentRPASystemRG --name PatentRPACluster --overwrite-existing
   ```

4. **Pod啟動失敗**
   ```bash
   # 檢查Pod日誌
   kubectl logs -f deployment/patent-rpa-backend -n patent-rpa-system
   
   # 檢查事件
   kubectl get events -n patent-rpa-system --sort-by='.lastTimestamp'
   ```

### 日誌位置

- **應用程式日誌**: Pod內的 `/app/logs` 目錄
- **Kubernetes事件**: `kubectl get events -n patent-rpa-system`
- **Pod日誌**: `kubectl logs <pod-name> -n patent-rpa-system`

## 系統架構

```
Internet → Azure Load Balancer → AKS Ingress Controller → Services
                                                        ├── Frontend (React)
                                                        ├── Backend (FastAPI)
                                                        └── RPA Bots (Selenium)
                                                             ↓
External APIs ← RPA Bots ← [TWPAT, USPTO, EPO, ...]
              ↓
Azure Services (PostgreSQL, Redis, OpenAI, AI Search)
```

## 安全配置

1. **密鑰管理**
   - 使用Kubernetes Secrets儲存敏感資訊
   - 配置Azure Key Vault整合
   - 避免在程式碼中硬編碼密鑰

2. **網路安全**
   - 配置適當的Network Policies
   - 限制Pod間通訊
   - 使用TLS加密所有外部通訊

3. **存取控制**
   - 配置RBAC權限
   - 使用Service Account
   - 定期輪換憑證

## 效能調優

1. **資源配置**
   - CPU: 根據工作負載調整requests和limits
   - Memory: 監控使用量並適當設定限制
   - Storage: 使用適當的StorageClass

2. **擴展性**
   - 配置Horizontal Pod Autoscaler (HPA)
   - 設定適當的副本數量
   - 使用Cluster Autoscaler自動擴展節點

## 維護作業

### 定期檢查

```bash
# 檢查系統資源使用
kubectl top nodes
kubectl top pods -n patent-rpa-system

# 檢查服務健康狀況
python3 monitor_deployment.py

# 更新容器映像
kubectl set image deployment/patent-rpa-backend backend=your-acr.azurecr.io/patent-rpa-backend:new-tag -n patent-rpa-system
```

### 備份和復原

1. **資料庫備份**
   - 設定定期PostgreSQL備份
   - 測試復原程序

2. **配置備份**
   - 匯出Kubernetes配置
   - 備份重要的ConfigMaps和Secrets

---

## 支援

如有問題或需要協助，請：

1. 檢查本文件的故障排除章節
2. 執行驗證腳本確認系統狀態
3. 使用監控腳本檢查詳細狀態
4. 檢查相關日誌檔案

更多詳細資訊請參考原始的MD檔案：
- `3_AZURE_DEPLOYMENT_CICD.md`
- `4_SYSTEM_TESTING_MONITORING.md`