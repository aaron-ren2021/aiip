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
kubectl get events -n patent-rpa-system --sort-by='.lastTimestamp'
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
