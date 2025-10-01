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
kubectl get events -n patent-rpa-system --sort-by='.lastTimestamp'

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
  python -c "import psycopg2; print('Database connection test')"

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
