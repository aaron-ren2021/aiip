#!/bin/bash

# Azure OpenAI 模型部署腳本
# RPA自動專利比對機器人系統

# ===========================================
# 配置變數 (請根據您的需求修改)
# ===========================================

# 從基礎設施腳本中取得的資源名稱
RESOURCE_GROUP="PatentRPASystemRG"
OPENAI_SERVICE_NAME="patent-rpa-openai-$RANDOM" # 請替換為實際的OpenAI服務名稱

# 模型部署配置
GPT4_DEPLOYMENT_NAME="gpt-4"
GPT4_MODEL_NAME="gpt-4"
GPT4_MODEL_VERSION="0613"
GPT4_CAPACITY=10

GPT35_DEPLOYMENT_NAME="gpt-35-turbo"
GPT35_MODEL_NAME="gpt-35-turbo"
GPT35_MODEL_VERSION="0613"
GPT35_CAPACITY=30

EMBEDDING_DEPLOYMENT_NAME="text-embedding-ada-002"
EMBEDDING_MODEL_NAME="text-embedding-ada-002"
EMBEDDING_MODEL_VERSION="2"
EMBEDDING_CAPACITY=30

# ===========================================
# 腳本開始
# ===========================================

set -e # 如果任何命令失敗，立即退出

echo "正在部署Azure OpenAI模型..."

# 登入Azure (如果尚未登入)
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "尚未登入Azure，正在引導您登入..."
    az login
fi

# --- 1. 部署GPT-4模型 ---
echo "正在部署GPT-4模型..."
az cognitiveservices account deployment create \
    --resource-group $RESOURCE_GROUP \
    --name $OPENAI_SERVICE_NAME \
    --deployment-name $GPT4_DEPLOYMENT_NAME \
    --model-name $GPT4_MODEL_NAME \
    --model-version $GPT4_MODEL_VERSION \
    --model-format OpenAI \
    --sku-capacity $GPT4_CAPACITY \
    --sku-name "Standard"

# --- 2. 部署GPT-3.5 Turbo模型 ---
echo "正在部署GPT-3.5 Turbo模型..."
az cognitiveservices account deployment create \
    --resource-group $RESOURCE_GROUP \
    --name $OPENAI_SERVICE_NAME \
    --deployment-name $GPT35_DEPLOYMENT_NAME \
    --model-name $GPT35_MODEL_NAME \
    --model-version $GPT35_MODEL_VERSION \
    --model-format OpenAI \
    --sku-capacity $GPT35_CAPACITY \
    --sku-name "Standard"

# --- 3. 部署文字嵌入模型 ---
echo "正在部署文字嵌入模型..."
az cognitiveservices account deployment create \
    --resource-group $RESOURCE_GROUP \
    --name $OPENAI_SERVICE_NAME \
    --deployment-name $EMBEDDING_DEPLOYMENT_NAME \
    --model-name $EMBEDDING_MODEL_NAME \
    --model-version $EMBEDDING_MODEL_VERSION \
    --model-format OpenAI \
    --sku-capacity $EMBEDDING_CAPACITY \
    --sku-name "Standard"

# --- 4. 驗證部署狀態 ---
echo "正在驗證模型部署狀態..."

echo "檢查GPT-4部署狀態..."
az cognitiveservices account deployment show \
    --resource-group $RESOURCE_GROUP \
    --name $OPENAI_SERVICE_NAME \
    --deployment-name $GPT4_DEPLOYMENT_NAME

echo "檢查GPT-3.5 Turbo部署狀態..."
az cognitiveservices account deployment show \
    --resource-group $RESOURCE_GROUP \
    --name $OPENAI_SERVICE_NAME \
    --deployment-name $GPT35_DEPLOYMENT_NAME

echo "檢查文字嵌入模型部署狀態..."
az cognitiveservices account deployment show \
    --resource-group $RESOURCE_GROUP \
    --name $OPENAI_SERVICE_NAME \
    --deployment-name $EMBEDDING_DEPLOYMENT_NAME

# --- 5. 取得端點和金鑰資訊 ---
OPENAI_ENDPOINT=$(az cognitiveservices account show --name $OPENAI_SERVICE_NAME --resource-group $RESOURCE_GROUP --query properties.endpoint -o tsv)
OPENAI_API_KEY=$(az cognitiveservices account keys list --name $OPENAI_SERVICE_NAME --resource-group $RESOURCE_GROUP --query key1 -o tsv)

# ===========================================
# 配置完成
# ===========================================

echo -e "\n\nAzure OpenAI模型部署完成！"
echo "============================================"
echo "OpenAI服務: $OPENAI_SERVICE_NAME"
echo "端點: $OPENAI_ENDPOINT"
echo "============================================"
echo "已部署的模型："
echo "- GPT-4: $GPT4_DEPLOYMENT_NAME (容量: $GPT4_CAPACITY TPM)"
echo "- GPT-3.5 Turbo: $GPT35_DEPLOYMENT_NAME (容量: $GPT35_CAPACITY TPM)"
echo "- 文字嵌入: $EMBEDDING_DEPLOYMENT_NAME (容量: $EMBEDDING_CAPACITY TPM)"
echo "============================================"
echo "重要：API金鑰已存儲在Key Vault中，請勿在程式碼中硬編碼。"

echo -e "\n測試API連接的範例："
echo "curl -H \"Content-Type: application/json\" \\"
echo "     -H \"api-key: $OPENAI_API_KEY\" \\"
echo "     -d '{\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}],\"max_tokens\":50}' \\"
echo "     \"$OPENAI_ENDPOINT/openai/deployments/$GPT35_DEPLOYMENT_NAME/chat/completions?api-version=2023-12-01-preview\""
