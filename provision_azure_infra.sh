#!/bin/bash

# Azure 基礎設施配置腳本
# RPA自動專利比對機器人系統

# ===========================================
# 配置變數 (請根據您的需求修改)
# ===========================================

# 資源群組
RESOURCE_GROUP="PatentRPASystemRG"
LOCATION="eastus" # 選擇離您最近的Azure區域

# Azure Container Registry (ACR)
ACR_NAME="patentRpaAcr$RANDOM" # ACR名稱必須是全域唯一的
ACR_SKU="Standard"

# Azure Kubernetes Service (AKS)
AKS_CLUSTER_NAME="PatentRPACluster"
AKS_NODE_COUNT=3
AKS_NODE_VM_SIZE="Standard_DS2_v2"
AKS_KUBERNETES_VERSION="1.28.5"

# Azure Database for PostgreSQL
POSTGRES_SERVER_NAME="patent-rpa-postgres-$RANDOM"
POSTGRES_ADMIN_USER="patent_admin"
POSTGRES_ADMIN_PASSWORD="your_secure_password_here_P@ssw0rd123!" # 請務必更換為高強度密碼
POSTGRES_SKU="B_Gen5_2" # Basic, 2 vCores
POSTGRES_VERSION="15"

# Azure Cache for Redis
REDIS_CACHE_NAME="patent-rpa-redis-$RANDOM"
REDIS_SKU="Basic"
REDIS_VM_SIZE="C0" # 250MB

# Azure AI Search
SEARCH_SERVICE_NAME="patent-rpa-search-$RANDOM"
SEARCH_SKU="basic"

# Azure OpenAI
OPENAI_SERVICE_NAME="patent-rpa-openai-$RANDOM"

# Azure Blob Storage
STORAGE_ACCOUNT_NAME="patentrpastorage$RANDOM"
STORAGE_CONTAINER_NAME="patent-documents"

# Azure Key Vault
KEY_VAULT_NAME="patent-rpa-keyvault-$RANDOM"

# ===========================================
# 腳本開始
# ===========================================

set -e # 如果任何命令失敗，立即退出

# 登入Azure (如果尚未登入)
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "尚未登入Azure，正在引導您登入..."
    az login
fi

# 取得當前登入的使用者ID
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)

# --- 1. 建立資源群組 ---
echo "正在建立資源群組: $RESOURCE_GROUP..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# --- 2. 建立Azure Container Registry (ACR) ---
echo "正在建立Azure Container Registry: $ACR_NAME..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku $ACR_SKU \
    --admin-enabled true

# --- 3. 建立Azure Kubernetes Service (AKS) ---
echo "正在建立Azure Kubernetes Service: $AKS_CLUSTER_NAME..."
az aks create \
    --resource-group $RESOURCE_GROUP \
    --name $AKS_CLUSTER_NAME \
    --node-count $AKS_NODE_COUNT \
    --node-vm-size $AKS_NODE_VM_SIZE \
    --kubernetes-version $AKS_KUBERNETES_VERSION \
    --enable-managed-identity \
    --generate-ssh-keys

# 授權AKS從ACR拉取映像
echo "正在授權AKS從ACR拉取映像..."
ACR_ID=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query id --output tsv)
AKS_SP_ID=$(az aks show --name $AKS_CLUSTER_NAME --resource-group $RESOURCE_GROUP --query identity.principalId --output tsv)
az role assignment create --assignee $AKS_SP_ID --scope $ACR_ID --role AcrPull

# --- 4. 建立Azure Database for PostgreSQL ---
echo "正在建立Azure Database for PostgreSQL: $POSTGRES_SERVER_NAME..."
az postgres flexible-server create \
    --resource-group $RESOURCE_GROUP \
    --name $POSTGRES_SERVER_NAME \
    --admin-user $POSTGRES_ADMIN_USER \
    --admin-password "$POSTGRES_ADMIN_PASSWORD" \
    --sku-name $POSTGRES_SKU \
    --version $POSTGRES_VERSION \
    --location $LOCATION \
    --public-access 0.0.0.0 # 允許所有Azure服務訪問，生產環境應更嚴格

# 建立資料庫
echo "正在建立PostgreSQL資料庫: patent_rpa..."
az postgres flexible-server db create \
    --resource-group $RESOURCE_GROUP \
    --server-name $POSTGRES_SERVER_NAME \
    --database-name patent_rpa

# --- 5. 建立Azure Cache for Redis ---
echo "正在建立Azure Cache for Redis: $REDIS_CACHE_NAME..."
az redis create \
    --resource-group $RESOURCE_GROUP \
    --name $REDIS_CACHE_NAME \
    --location $LOCATION \
    --sku $REDIS_SKU \
    --vm-size $REDIS_VM_SIZE

# --- 6. 建立Azure AI Search ---
echo "正在建立Azure AI Search: $SEARCH_SERVICE_NAME..."
az search service create \
    --resource-group $RESOURCE_GROUP \
    --name $SEARCH_SERVICE_NAME \
    --sku $SEARCH_SKU \
    --location $LOCATION

# --- 7. 建立Azure OpenAI ---
echo "正在建立Azure OpenAI服務: $OPENAI_SERVICE_NAME..."
az cognitiveservices account create \
    --resource-group $RESOURCE_GROUP \
    --name $OPENAI_SERVICE_NAME \
    --location $LOCATION \
    --kind OpenAI \
    --sku S0

# --- 8. 建立Azure Blob Storage ---
echo "正在建立Azure Blob Storage: $STORAGE_ACCOUNT_NAME..."
az storage account create \
    --resource-group $RESOURCE_GROUP \
    --name $STORAGE_ACCOUNT_NAME \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2

# 取得連接字串
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP -o tsv)

# 建立容器
echo "正在建立Blob容器: $STORAGE_CONTAINER_NAME..."
az storage container create \
    --name $STORAGE_CONTAINER_NAME \
    --connection-string "$STORAGE_CONNECTION_STRING" \
    --public-access blob

# --- 9. 建立Azure Key Vault ---
echo "正在建立Azure Key Vault: $KEY_VAULT_NAME..."
az keyvault create \
    --resource-group $RESOURCE_GROUP \
    --name $KEY_VAULT_NAME \
    --location $LOCATION \
    --enable-rbac-authorization true

# 授權自己管理Key Vault
echo "正在授權使用者管理Key Vault..."
az role assignment create \
    --role "Key Vault Administrator" \
    --assignee $USER_OBJECT_ID \
    --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME"

# --- 10. 將敏感資訊存入Key Vault ---
echo "正在將敏感資訊存入Key Vault..."

# 等待Key Vault權限生效
sleep 30

az keyvault secret set --vault-name $KEY_VAULT_NAME --name "PostgresPassword" --value "$POSTGRES_ADMIN_PASSWORD"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "RedisConnectionString" --value "$(az redis list-keys --name $REDIS_CACHE_NAME --resource-group $RESOURCE_GROUP --query primaryKey -o tsv)"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "AcrAdminPassword" --value "$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "StorageConnectionString" --value "$STORAGE_CONNECTION_STRING"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "SearchApiKey" --value "$(az search admin-key show --service-name $SEARCH_SERVICE_NAME --resource-group $RESOURCE_GROUP --query primaryKey -o tsv)"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "OpenAiApiKey" --value "$(az cognitiveservices account keys list --name $OPENAI_SERVICE_NAME --resource-group $RESOURCE_GROUP --query key1 -o tsv)"

# ===========================================
# 配置完成
# ===========================================

echo -e "\n\nAzure基礎設施配置完成！"
echo "============================================"
echo "資源群組: $RESOURCE_GROUP"
echo "ACR名稱: $ACR_NAME"
echo "AKS叢集名稱: $AKS_CLUSTER_NAME"
echo "PostgreSQL伺服器: $POSTGRES_SERVER_NAME"
echo "Redis快取: $REDIS_CACHE_NAME"
echo "AI Search服務: $SEARCH_SERVICE_NAME"
echo "OpenAI服務: $OPENAI_SERVICE_NAME"
echo "儲存體帳戶: $STORAGE_ACCOUNT_NAME"
echo "Key Vault: $KEY_VAULT_NAME"
echo "============================================"
echo "重要：請妥善保管您的PostgreSQL管理員密碼。"
echo "所有其他敏感資訊已存儲在Key Vault中。"


