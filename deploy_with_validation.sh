#!/bin/bash

# 增強版部署腳本 - 包含預檢查
# RPA自動專利比對機器人系統

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查必要工具
check_prerequisites() {
    log_info "檢查必要工具..."
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    # 檢查 kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝，請先安裝 kubectl"
        exit 1
    fi
    
    # 檢查 Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI 未安裝，請先安裝 Azure CLI"
        exit 1
    fi
    
    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安裝"
        exit 1
    fi
    
    log_success "所有必要工具都已安裝"
}

# 運行驗證腳本
run_validation() {
    log_info "運行部署驗證檢查..."
    
    if python3 validate_deployment.py; then
        log_success "驗證檢查通過"
    else
        log_warning "驗證檢查發現問題，但繼續部署..."
        log_warning "建議修復問題後重新部署"
        sleep 5
    fi
}

# 檢查Azure登入狀態
check_azure_login() {
    log_info "檢查Azure登入狀態..."
    
    if ! az account show &> /dev/null; then
        log_error "尚未登入Azure，請執行: az login"
        exit 1
    fi
    
    local subscription=$(az account show --query name -o tsv)
    log_success "已登入Azure訂用帳戶: $subscription"
}

# 設定配置變數
setup_config() {
    log_info "設定部署配置..."
    
    # 從環境變數或使用預設值
    export RESOURCE_GROUP="${RESOURCE_GROUP:-PatentRPASystemRG}"
    export AKS_CLUSTER_NAME="${AKS_CLUSTER_NAME:-PatentRPACluster}"
    export ACR_NAME="${ACR_NAME:-patentRpaAcr}"
    export NAMESPACE="${NAMESPACE:-patent-rpa-system}"
    export IMAGE_TAG="${1:-latest}"
    
    log_info "資源群組: $RESOURCE_GROUP"
    log_info "AKS叢集: $AKS_CLUSTER_NAME"
    log_info "容器登錄: $ACR_NAME"
    log_info "命名空間: $NAMESPACE"
    log_info "映像標籤: $IMAGE_TAG"
}

# 連接到AKS叢集
connect_to_aks() {
    log_info "連接到AKS叢集..."
    
    if ! az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER_NAME" --overwrite-existing; then
        log_error "無法連接到AKS叢集，請檢查叢集是否存在"
        exit 1
    fi
    
    # 測試連接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到Kubernetes叢集"
        exit 1
    fi
    
    log_success "成功連接到AKS叢集"
}

# 準備ACR登入密鑰
setup_acr_secret() {
    log_info "設定ACR登入密鑰..."
    
    local acr_server=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv 2>/dev/null || echo "")
    
    if [ -z "$acr_server" ]; then
        log_error "找不到ACR: $ACR_NAME"
        exit 1
    fi
    
    local acr_username=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
    local acr_password=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)
    
    # 建立或更新密鑰
    kubectl create secret docker-registry acr-secret \
        --namespace="$NAMESPACE" \
        --docker-server="$acr_server" \
        --docker-username="$acr_username" \
        --docker-password="$acr_password" \
        --dry-run=client -o yaml | kubectl apply -f - || {
        log_error "設定ACR密鑰失敗"
        exit 1
    }
    
    log_success "ACR登入密鑰設定完成"
}

# 部署Kubernetes資源
deploy_k8s_resources() {
    log_info "部署Kubernetes資源..."
    
    # 建立臨時目錄並複製配置檔案
    local temp_dir=$(mktemp -d)
    cp -r azure-config/k8s/* "$temp_dir/"
    
    # 取得ACR伺服器名稱
    local acr_server=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)
    
    # 替換映像標籤
    sed -i "s|patentRpaAcr.azurecr.io|$acr_server|g" "$temp_dir"/*.yaml
    sed -i "s|:latest|:$IMAGE_TAG|g" "$temp_dir"/*.yaml
    
    # 按順序部署資源
    log_info "建立命名空間..."
    kubectl apply -f "$temp_dir/namespace.yaml"
    
    log_info "部署ConfigMap和Secret..."
    kubectl apply -f "$temp_dir/configmap.yaml"
    kubectl apply -f "$temp_dir/secret.yaml"
    
    log_info "部署應用程式..."
    kubectl apply -f "$temp_dir/backend-deployment.yaml"
    kubectl apply -f "$temp_dir/rpa-deployment.yaml"
    kubectl apply -f "$temp_dir/frontend-deployment.yaml"
    
    # 清理臨時目錄
    rm -rf "$temp_dir"
    
    log_success "Kubernetes資源部署完成"
}

# 等待部署完成
wait_for_deployment() {
    log_info "等待部署完成..."
    
    local deployments=("patent-rpa-backend" "patent-rpa-bots" "patent-rpa-frontend")
    
    for deployment in "${deployments[@]}"; do
        log_info "等待 $deployment 就緒..."
        if kubectl wait --for=condition=available --timeout=300s deployment/"$deployment" -n "$NAMESPACE"; then
            log_success "$deployment 部署成功"
        else
            log_error "$deployment 部署超時"
            return 1
        fi
    done
}

# 檢查部署狀態
check_deployment_status() {
    log_info "檢查部署狀態..."
    
    echo "=== Pods 狀態 ==="
    kubectl get pods -n "$NAMESPACE"
    
    echo -e "\n=== Services 狀態 ==="
    kubectl get services -n "$NAMESPACE"
    
    echo -e "\n=== Ingress 狀態 ==="
    kubectl get ingress -n "$NAMESPACE" 2>/dev/null || echo "無Ingress資源"
}

# 執行健康檢查
health_check() {
    log_info "執行健康檢查..."
    sleep 30
    
    local backend_pod=$(kubectl get pods -n "$NAMESPACE" -l app=patent-rpa-backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$backend_pod" ]; then
        log_info "測試後端API健康檢查..."
        if kubectl exec "$backend_pod" -n "$NAMESPACE" -- curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "後端API健康檢查通過"
        else
            log_warning "後端API健康檢查失敗"
        fi
    else
        log_warning "找不到後端Pod"
    fi
}

# 主函數
main() {
    echo "🚀 RPA專利比對系統部署腳本"
    echo "=================================="
    
    # 檢查前置條件
    check_prerequisites
    
    # 運行驗證
    run_validation
    
    # 檢查Azure登入
    check_azure_login
    
    # 設定配置
    setup_config "$@"
    
    # 連接到AKS
    connect_to_aks
    
    # 設定ACR密鑰
    setup_acr_secret
    
    # 部署資源
    deploy_k8s_resources
    
    # 等待部署完成
    if wait_for_deployment; then
        log_success "所有部署都已完成"
    else
        log_error "部分部署失敗"
        check_deployment_status
        exit 1
    fi
    
    # 檢查狀態
    check_deployment_status
    
    # 健康檢查
    health_check
    
    echo
    log_success "🎉 部署完成！"
    echo "=================================="
    echo "命名空間: $NAMESPACE"
    echo "映像標籤: $IMAGE_TAG"
    echo "=================================="
    echo "使用以下命令監控系統狀態："
    echo "kubectl get pods -n $NAMESPACE -w"
    echo "kubectl logs -f deployment/patent-rpa-backend -n $NAMESPACE"
}

# 執行主函數
main "$@"