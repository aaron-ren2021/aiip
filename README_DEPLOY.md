# AIIP Azure 一鍵部署指南

此檔案說明如何使用新加入的 `deploy_full.sh` 與 `.azure-deploy.env` 進行端到端部署。

## 檔案說明
| 檔案 | 用途 |
| ---- | ---- |
| `.azure-deploy.env` | 集中管理所有 Azure 資源命名與參數 |
| `deploy_full.sh` | 一鍵或分階段部署協調腳本 |

## 前置需求
1. 已安裝 Azure CLI, Docker, kubectl
2. 具有目標訂用帳戶的 Contributor 權限以上
3. 登入 `az login`

## 編輯環境變數
開啟 `.azure-deploy.env`，確認或調整必要參數：
```
SUBSCRIPTION_ID=0e79512a-30a6-4276-8c8d-55bef5df741b
LOCATION=eastus
NAME_PREFIX=aiip
...其餘資源名稱...
```

## 授予腳本執行權限
```
chmod +x deploy_full.sh provision_azure_infra.sh setup_ai_search.sh deploy_openai_models.sh deploy_to_aks.sh setup_monitoring.sh
```

## 全流程一鍵部署
```
./deploy_full.sh all
```
（流程：infra → openai → search → images → aks → monitor → validate）

## 分階段部署
```
./deploy_full.sh infra
./deploy_full.sh openai
./deploy_full.sh search
./deploy_full.sh images
./deploy_full.sh aks
./deploy_full.sh monitor
./deploy_full.sh validate
```

## 重新執行注意事項
資源名稱已固定（無 $RANDOM），重複執行 `infra` 若資源已存在會報錯，可：
- 手動刪除資源群組重新建立，或
- 修改 `.azure-deploy.env` 中名稱，或
- 跳過已完成階段

## 影像建置說明
目前僅有單一 `Dockerfile`（後端基底），前端與 RPA Bots 暫用同一份映像建置流程，可未來拆分：
```
docker build -t $ACR_NAME.azurecr.io/patent-rpa-backend:latest -f Dockerfile .
```
若日後新增 `frontend/Dockerfile`、`rpa/Dockerfile`，請調整 `deploy_full.sh` 的 `phase_images` 區段。

## 驗證
部署完成後：
```
kubectl get pods -n patent-rpa-system
kubectl get ingress -n patent-rpa-system
```
如 ingress 尚無 IP，等待數分鐘再查詢。

## 常見問題
1. ACR 名稱衝突：修改 `.azure-deploy.env` 的 `ACR_NAME` 後重新執行 `images` → `aks`
2. OpenAI 模型無法部署：確認該 Region 配額，或將 `ENABLE_GPT4=false`
3. Search 建立失敗：確保服務名稱無被佔用，或已成功建立於同 region。

---
此指南會與原始的 `1_AZURE_INFRA_SETUP.md` ~ `4_SYSTEM_TESTING_MONITORING.md` 搭配使用。
