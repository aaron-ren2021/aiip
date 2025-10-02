#!/bin/bash

# Azure 監控與日誌配置腳本
# RPA自動專利比對機器人系統

# ===========================================
# 配置變數 (請根據您的需求修改)
# ===========================================

# 從基礎設施腳本中取得的資源名稱
RESOURCE_GROUP="PatentRPASystemRG"
AKS_CLUSTER_NAME="PatentRPACluster"
LOCATION="eastus"

# Application Insights
APP_INSIGHTS_NAME="patent-rpa-insights"

# Log Analytics Workspace
LOG_ANALYTICS_NAME="patent-rpa-logs"

# Azure Monitor Action Group
ACTION_GROUP_NAME="patent-rpa-alerts"
NOTIFICATION_EMAIL="admin@your-company.com" # 請替換為實際的通知郵箱

# ===========================================
# 腳本開始
# ===========================================

set -e # 如果任何命令失敗，立即退出

echo "正在配置Azure監控與日誌服務..."

# 登入Azure (如果尚未登入)
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "尚未登入Azure，正在引導您登入..."
    az login
fi

# --- 1. 建立Log Analytics Workspace ---
echo "正在建立Log Analytics Workspace: $LOG_ANALYTICS_NAME..."
az monitor log-analytics workspace create \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_NAME \
    --location $LOCATION \
    --sku PerGB2018

# 取得Workspace ID和金鑰
WORKSPACE_ID=$(az monitor log-analytics workspace show \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_NAME \
    --query customerId -o tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_NAME \
    --query primarySharedKey -o tsv)

# --- 2. 建立Application Insights ---
echo "正在建立Application Insights: $APP_INSIGHTS_NAME..."
az monitor app-insights component create \
    --app $APP_INSIGHTS_NAME \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --workspace $LOG_ANALYTICS_NAME

# 取得Application Insights連接字串
APP_INSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
    --app $APP_INSIGHTS_NAME \
    --resource-group $RESOURCE_GROUP \
    --query connectionString -o tsv)

# --- 3. 為AKS啟用監控 ---
echo "正在為AKS叢集啟用監控..."
az aks enable-addons \
    --resource-group $RESOURCE_GROUP \
    --name $AKS_CLUSTER_NAME \
    --addons monitoring \
    --workspace-resource-id "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.OperationalInsights/workspaces/$LOG_ANALYTICS_NAME"

# --- 4. 建立Action Group ---
echo "正在建立Action Group: $ACTION_GROUP_NAME..."
az monitor action-group create \
    --resource-group $RESOURCE_GROUP \
    --name $ACTION_GROUP_NAME \
    --short-name "PatentRPA" \
    --email-receivers name="Admin" email="$NOTIFICATION_EMAIL"

# --- 5. 建立告警規則 ---
echo "正在建立告警規則..."

# CPU使用率過高告警
az monitor metrics alert create \
    --name "High CPU Usage - Patent RPA" \
    --resource-group $RESOURCE_GROUP \
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/$AKS_CLUSTER_NAME" \
    --condition "avg Percentage CPU > 80" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --action $ACTION_GROUP_NAME \
    --description "CPU使用率超過80%"

# 記憶體使用率過高告警
az monitor metrics alert create \
    --name "High Memory Usage - Patent RPA" \
    --resource-group $RESOURCE_GROUP \
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/$AKS_CLUSTER_NAME" \
    --condition "avg Percentage Memory > 85" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --action $ACTION_GROUP_NAME \
    --description "記憶體使用率超過85%"

# Pod重啟次數過多告警
az monitor metrics alert create \
    --name "Pod Restart Alert - Patent RPA" \
    --resource-group $RESOURCE_GROUP \
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/$AKS_CLUSTER_NAME" \
    --condition "total Restart Count > 5" \
    --window-size 15m \
    --evaluation-frequency 5m \
    --action $ACTION_GROUP_NAME \
    --description "Pod重啟次數在15分鐘內超過5次"

# --- 6. 建立自訂儀表板 ---
echo "正在建立Azure儀表板..."

cat > dashboard.json << EOF
{
    "lenses": {
        "0": {
            "order": 0,
            "parts": {
                "0": {
                    "position": {
                        "x": 0,
                        "y": 0,
                        "colSpan": 6,
                        "rowSpan": 4
                    },
                    "metadata": {
                        "inputs": [
                            {
                                "name": "resourceTypeMode",
                                "isOptional": true
                            },
                            {
                                "name": "ComponentId",
                                "value": "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/$AKS_CLUSTER_NAME",
                                "isOptional": true
                            }
                        ],
                        "type": "Extension/HubsExtension/PartType/MonitorChartPart",
                        "settings": {
                            "content": {
                                "options": {
                                    "chart": {
                                        "metrics": [
                                            {
                                                "resourceMetadata": {
                                                    "id": "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/$AKS_CLUSTER_NAME"
                                                },
                                                "name": "node_cpu_usage_percentage",
                                                "aggregationType": 4,
                                                "namespace": "microsoft.containerservice/managedclusters",
                                                "metricVisualization": {
                                                    "displayName": "CPU使用率"
                                                }
                                            }
                                        ],
                                        "title": "AKS叢集CPU使用率",
                                        "titleKind": 1,
                                        "visualization": {
                                            "chartType": 2,
                                            "legendVisualization": {
                                                "isVisible": true,
                                                "position": 2,
                                                "hideSubtitle": false
                                            },
                                            "axisVisualization": {
                                                "x": {
                                                    "isVisible": true,
                                                    "axisType": 2
                                                },
                                                "y": {
                                                    "isVisible": true,
                                                    "axisType": 1
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "metadata": {
        "model": {
            "timeRange": {
                "value": {
                    "relative": {
                        "duration": 24,
                        "timeUnit": 1
                    }
                },
                "type": "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
            },
            "filterLocale": {
                "value": "zh-tw"
            },
            "filters": {
                "value": {
                    "MsPortalFx_TimeRange": {
                        "model": {
                            "format": "utc",
                            "granularity": "auto",
                            "relative": "24h"
                        },
                        "displayCache": {
                            "name": "UTC Time",
                            "value": "過去 24 小時"
                        },
                        "filteredPartIds": []
                    }
                }
            }
        }
    }
}
EOF

az portal dashboard create \
    --resource-group $RESOURCE_GROUP \
    --name "Patent RPA System Dashboard" \
    --input-path dashboard.json

# --- 7. 建立Kusto查詢 ---
echo "正在建立常用的Log Analytics查詢..."

cat > queries.kql << 'EOF'
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

// 查詢4: 檢視RPA機器人執行狀態
ContainerLog
| where Name contains "rpa-bots"
| where LogEntry contains "Robot" or LogEntry contains "Search"
| project TimeGenerated, LogEntry
| order by TimeGenerated desc
| take 50

// 查詢5: 資源使用率趨勢
Perf
| where ObjectName == "K8SContainer"
| where CounterName == "cpuUsageNanoCores" or CounterName == "memoryWorkingSetBytes"
| summarize avg(CounterValue) by bin(TimeGenerated, 10m), CounterName, InstanceName
| order by TimeGenerated desc
EOF

echo "Log Analytics查詢已儲存到 queries.kql 檔案中"

# --- 8. 清理暫存檔案 ---
rm -f dashboard.json

# ===========================================
# 配置完成
# ===========================================

echo -e "\n\nAzure監控配置完成！"
echo "============================================"
echo "Log Analytics Workspace: $LOG_ANALYTICS_NAME"
echo "Application Insights: $APP_INSIGHTS_NAME"
echo "Action Group: $ACTION_GROUP_NAME"
echo "Workspace ID: $WORKSPACE_ID"
echo "============================================"
echo "重要資訊："
echo "- Application Insights連接字串已配置"
echo "- AKS叢集監控已啟用"
echo "- 告警規則已建立"
echo "- 自訂儀表板已建立"

echo -e "\n連接字串 (請加入到應用程式配置中)："
echo "AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING=\"$APP_INSIGHTS_CONNECTION_STRING\""

echo -e "\nKubernetes監控配置："
echo "WORKSPACE_ID=\"$WORKSPACE_ID\""
echo "WORKSPACE_KEY=\"$WORKSPACE_KEY\""

echo -e "\n有用的監控連結："
echo "- Azure Portal儀表板: https://portal.azure.com/#@/dashboard/arm/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Portal/dashboards/Patent%20RPA%20System%20Dashboard"
echo "- Log Analytics: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.OperationalInsights/workspaces/$LOG_ANALYTICS_NAME/logs"
echo "- Application Insights: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Insights/components/$APP_INSIGHTS_NAME/overview"

echo -e "\n常用監控命令："
echo "# 檢視AKS叢集健康狀態"
echo "kubectl get nodes"
echo "kubectl get pods -n patent-rpa-system"
echo ""
echo "# 檢視資源使用情況"
echo "kubectl top nodes"
echo "kubectl top pods -n patent-rpa-system"
echo ""
echo "# 檢視Pod日誌"
echo "kubectl logs -f deployment/patent-rpa-backend -n patent-rpa-system"
