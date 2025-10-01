#!/bin/bash

# Azure Kubernetes Service 部署腳本
# RPA自動專利比對機器人系統

# ===========================================
# 配置變數 (請根據您的需求修改)
# ===========================================

# 從基礎設施腳本中取得的資源名稱
RESOURCE_GROUP="PatentRPASystemRG"
AKS_CLUSTER_NAME="PatentRPACluster"
ACR_NAME="patentRpaAcr" # 請替換為實際的ACR名稱
NAMESPACE="patent-rpa-system"

# Docker映像標籤
IMAGE_TAG="${1:-latest}" # 可以通過命令列參數指定標籤，預設為latest

# ===========================================
# 腳本開始
# ===========================================

set -e # 如果任何命令失敗，立即退出

echo "正在部署RPA專利比對系統到Azure Kubernetes Service..."
echo "映像標籤: $IMAGE_TAG"

# 登入Azure (如果尚未登入)
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "尚未登入Azure，正在引導您登入..."
    az login
fi

# --- 1. 連接到AKS叢集 ---
echo "正在連接到AKS叢集: $AKS_CLUSTER_NAME..."
az aks get-credentials \
    --resource-group $RESOURCE_GROUP \
    --name $AKS_CLUSTER_NAME \
    --overwrite-existing

# --- 2. 建立ACR登入密鑰 ---
echo "正在建立ACR登入密鑰..."
ACR_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

kubectl create secret docker-registry acr-secret \
    --namespace=$NAMESPACE \
    --docker-server=$ACR_SERVER \
    --docker-username=$ACR_USERNAME \
    --docker-password=$ACR_PASSWORD \
    --dry-run=client -o yaml | kubectl apply -f -

# --- 3. 更新Kubernetes配置檔案中的映像標籤 ---
echo "正在更新Kubernetes配置檔案..."

# 建立臨時目錄
TEMP_DIR=$(mktemp -d)
cp -r azure-config/k8s/* $TEMP_DIR/

# 替換映像標籤
sed -i "s|patentRpaAcr.azurecr.io/patent-rpa-backend:latest|$ACR_SERVER/patent-rpa-backend:$IMAGE_TAG|g" $TEMP_DIR/*.yaml
sed -i "s|patentRpaAcr.azurecr.io/patent-rpa-frontend:latest|$ACR_SERVER/patent-rpa-frontend:$IMAGE_TAG|g" $TEMP_DIR/*.yaml
sed -i "s|patentRpaAcr.azurecr.io/patent-rpa-bots:latest|$ACR_SERVER/patent-rpa-bots:$IMAGE_TAG|g" $TEMP_DIR/*.yaml

# --- 4. 部署到Kubernetes ---
echo "正在部署到Kubernetes..."

# 建立命名空間
kubectl apply -f $TEMP_DIR/namespace.yaml

# 部署ConfigMap和Secret
kubectl apply -f $TEMP_DIR/configmap.yaml
kubectl apply -f $TEMP_DIR/secret.yaml

# 部署應用程式
kubectl apply -f $TEMP_DIR/backend-deployment.yaml
kubectl apply -f $TEMP_DIR/rpa-deployment.yaml
kubectl apply -f $TEMP_DIR/frontend-deployment.yaml

# --- 5. 等待部署完成 ---
echo "正在等待部署完成..."

echo "等待後端服務就緒..."
kubectl wait --for=condition=available --timeout=300s deployment/patent-rpa-backend -n $NAMESPACE

echo "等待RPA機器人服務就緒..."
kubectl wait --for=condition=available --timeout=300s deployment/patent-rpa-bots -n $NAMESPACE

echo "等待前端服務就緒..."
kubectl wait --for=condition=available --timeout=300s deployment/patent-rpa-frontend -n $NAMESPACE

# --- 6. 檢查部署狀態 ---
echo "正在檢查部署狀態..."

echo "=== Pods 狀態 ==="
kubectl get pods -n $NAMESPACE

echo "=== Services 狀態 ==="
kubectl get services -n $NAMESPACE

echo "=== Ingress 狀態 ==="
kubectl get ingress -n $NAMESPACE

# --- 7. 取得應用程式URL ---
echo "正在取得應用程式URL..."

INGRESS_IP=$(kubectl get ingress patent-rpa-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "尚未分配")
if [ "$INGRESS_IP" != "尚未分配" ] && [ "$INGRESS_IP" != "" ]; then
    echo "應用程式URL: http://$INGRESS_IP"
else
    echo "Ingress IP尚未分配，請稍後檢查："
    echo "kubectl get ingress patent-rpa-ingress -n $NAMESPACE"
fi

# --- 8. 顯示有用的命令 ---
echo -e "\n=== 有用的管理命令 ==="
echo "檢查Pod日誌："
echo "kubectl logs -f deployment/patent-rpa-backend -n $NAMESPACE"
echo "kubectl logs -f deployment/patent-rpa-bots -n $NAMESPACE"
echo "kubectl logs -f deployment/patent-rpa-frontend -n $NAMESPACE"

echo -e "\n檢查Pod狀態："
echo "kubectl get pods -n $NAMESPACE -w"

echo -e "\n進入Pod進行除錯："
echo "kubectl exec -it deployment/patent-rpa-backend -n $NAMESPACE -- /bin/bash"

echo -e "\n檢查服務端點："
echo "kubectl get endpoints -n $NAMESPACE"

echo -e "\n重新啟動部署："
echo "kubectl rollout restart deployment/patent-rpa-backend -n $NAMESPACE"
echo "kubectl rollout restart deployment/patent-rpa-bots -n $NAMESPACE"
echo "kubectl rollout restart deployment/patent-rpa-frontend -n $NAMESPACE"

# --- 9. 清理臨時檔案 ---
rm -rf $TEMP_DIR

# ===========================================
# 部署完成
# ===========================================

echo -e "\n\n部署完成！"
echo "============================================"
echo "命名空間: $NAMESPACE"
echo "映像標籤: $IMAGE_TAG"
echo "ACR伺服器: $ACR_SERVER"
echo "============================================"
echo "請等待幾分鐘讓所有服務完全啟動。"
echo "您可以使用上述命令監控部署狀態。"

# 執行基本健康檢查
echo -e "\n正在執行基本健康檢查..."
sleep 30

BACKEND_POD=$(kubectl get pods -n $NAMESPACE -l app=patent-rpa-backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ "$BACKEND_POD" != "" ]; then
    echo "測試後端API健康檢查..."
    kubectl exec $BACKEND_POD -n $NAMESPACE -- curl -f http://localhost:8000/health 2>/dev/null && echo "後端API健康檢查通過" || echo "後端API健康檢查失敗"
fi

RPA_POD=$(kubectl get pods -n $NAMESPACE -l app=patent-rpa-bots -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ "$RPA_POD" != "" ]; then
    echo "測試RPA服務健康檢查..."
    kubectl exec $RPA_POD -n $NAMESPACE -- curl -f http://localhost:8001/health 2>/dev/null && echo "RPA服務健康檢查通過" || echo "RPA服務健康檢查失敗"
fi

echo -e "\n部署腳本執行完成！"
