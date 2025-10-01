#!/bin/bash

# Azure AI Search 與認知服務整合配置腳本
# RPA自動專利比對機器人系統

# ===========================================
# 配置變數 (請根據您的需求修改)
# ===========================================

# 從基礎設施腳本中取得的資源名稱
RESOURCE_GROUP="PatentRPASystemRG"
SEARCH_SERVICE_NAME="patent-rpa-search-$RANDOM" # 請替換為實際的搜尋服務名稱
STORAGE_ACCOUNT_NAME="patentrpastorage$RANDOM" # 請替換為實際的儲存體帳戶名稱
OPENAI_SERVICE_NAME="patent-rpa-openai-$RANDOM" # 請替換為實際的OpenAI服務名稱
KEY_VAULT_NAME="patent-rpa-keyvault-$RANDOM" # 請替換為實際的Key Vault名稱

# 索引配置
PATENT_INDEX_NAME="patent-documents"
DATASOURCE_NAME="patent-blob-datasource"
INDEXER_NAME="patent-blob-indexer"
SKILLSET_NAME="patent-cognitive-skillset"

# Blob容器名稱
CONTAINER_NAME="patent-documents"

# ===========================================
# 腳本開始
# ===========================================

set -e # 如果任何命令失敗，立即退出

echo "正在配置Azure AI Search與認知服務整合..."

# 登入Azure (如果尚未登入)
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "尚未登入Azure，正在引導您登入..."
    az login
fi

# 取得必要的連接資訊
echo "正在取得服務連接資訊..."
SEARCH_API_KEY=$(az search admin-key show --service-name $SEARCH_SERVICE_NAME --resource-group $RESOURCE_GROUP --query primaryKey -o tsv)
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP -o tsv)
OPENAI_API_KEY=$(az cognitiveservices account keys list --name $OPENAI_SERVICE_NAME --resource-group $RESOURCE_GROUP --query key1 -o tsv)
OPENAI_ENDPOINT=$(az cognitiveservices account show --name $OPENAI_SERVICE_NAME --resource-group $RESOURCE_GROUP --query properties.endpoint -o tsv)

# --- 1. 建立資料來源 (Data Source) ---
echo "正在建立Blob儲存體資料來源..."

cat > datasource.json << EOF
{
    "name": "$DATASOURCE_NAME",
    "description": "專利文件Blob儲存體資料來源",
    "type": "azureblob",
    "credentials": {
        "connectionString": "$STORAGE_CONNECTION_STRING"
    },
    "container": {
        "name": "$CONTAINER_NAME",
        "query": null
    },
    "dataChangeDetectionPolicy": {
        "@odata.type": "#Microsoft.Azure.Search.HighWaterMarkChangeDetectionPolicy",
        "highWaterMarkColumnName": "_ts"
    },
    "dataDeletionDetectionPolicy": {
        "@odata.type": "#Microsoft.Azure.Search.SoftDeleteColumnDeletionDetectionPolicy",
        "softDeleteColumnName": "isDeleted",
        "softDeleteMarkerValue": "true"
    }
}
EOF

curl -X POST \
    "https://$SEARCH_SERVICE_NAME.search.windows.net/datasources?api-version=2023-11-01" \
    -H "Content-Type: application/json" \
    -H "api-key: $SEARCH_API_KEY" \
    -d @datasource.json

# --- 2. 建立認知技能集 (Skillset) ---
echo "正在建立認知技能集..."

cat > skillset.json << EOF
{
    "name": "$SKILLSET_NAME",
    "description": "專利文件處理認知技能集",
    "skills": [
        {
            "@odata.type": "#Microsoft.Skills.Text.SplitSkill",
            "name": "SplitSkill",
            "description": "將文件分割成較小的區塊",
            "context": "/document",
            "defaultLanguageCode": "zh-Hant",
            "textSplitMode": "pages",
            "maximumPageLength": 2000,
            "pageOverlapLength": 200,
            "inputs": [
                {
                    "name": "text",
                    "source": "/document/content"
                }
            ],
            "outputs": [
                {
                    "name": "textItems",
                    "targetName": "pages"
                }
            ]
        },
        {
            "@odata.type": "#Microsoft.Skills.Text.V3.EntityRecognitionSkill",
            "name": "EntityRecognitionSkill",
            "description": "識別專利文件中的實體",
            "context": "/document/pages/*",
            "categories": ["Person", "Organization", "Location", "DateTime"],
            "defaultLanguageCode": "zh-Hant",
            "inputs": [
                {
                    "name": "text",
                    "source": "/document/pages/*"
                }
            ],
            "outputs": [
                {
                    "name": "persons",
                    "targetName": "persons"
                },
                {
                    "name": "organizations",
                    "targetName": "organizations"
                },
                {
                    "name": "locations",
                    "targetName": "locations"
                },
                {
                    "name": "dateTimes",
                    "targetName": "dateTimes"
                }
            ]
        },
        {
            "@odata.type": "#Microsoft.Skills.Text.KeyPhraseExtractionSkill",
            "name": "KeyPhraseExtractionSkill",
            "description": "提取關鍵詞組",
            "context": "/document/pages/*",
            "defaultLanguageCode": "zh-Hant",
            "inputs": [
                {
                    "name": "text",
                    "source": "/document/pages/*"
                }
            ],
            "outputs": [
                {
                    "name": "keyPhrases",
                    "targetName": "keyPhrases"
                }
            ]
        },
        {
            "@odata.type": "#Microsoft.Skills.Vision.OcrSkill",
            "name": "OcrSkill",
            "description": "從圖片中提取文字",
            "context": "/document/normalized_images/*",
            "defaultLanguageCode": "zh-Hant",
            "detectOrientation": true,
            "inputs": [
                {
                    "name": "image",
                    "source": "/document/normalized_images/*"
                }
            ],
            "outputs": [
                {
                    "name": "text",
                    "targetName": "text"
                }
            ]
        },
        {
            "@odata.type": "#Microsoft.Skills.Util.DocumentExtractionSkill",
            "name": "DocumentExtractionSkill",
            "description": "從PDF等文件中提取內容",
            "context": "/document",
            "parsingMode": "default",
            "dataToExtract": "contentAndMetadata",
            "configuration": {
                "imageAction": "generateNormalizedImages",
                "normalizedImageMaxWidth": 2000,
                "normalizedImageMaxHeight": 2000
            },
            "inputs": [
                {
                    "name": "file_data",
                    "source": "/document/file_data"
                }
            ],
            "outputs": [
                {
                    "name": "content",
                    "targetName": "content"
                },
                {
                    "name": "normalized_images",
                    "targetName": "normalized_images"
                }
            ]
        }
    ],
    "cognitiveServices": {
        "@odata.type": "#Microsoft.Azure.Search.CognitiveServicesByKey",
        "description": "認知服務資源",
        "key": "$OPENAI_API_KEY"
    }
}
EOF

curl -X POST \
    "https://$SEARCH_SERVICE_NAME.search.windows.net/skillsets?api-version=2023-11-01" \
    -H "Content-Type: application/json" \
    -H "api-key: $SEARCH_API_KEY" \
    -d @skillset.json

# --- 3. 建立索引 (Index) ---
echo "正在建立專利文件索引..."

cat > index.json << EOF
{
    "name": "$PATENT_INDEX_NAME",
    "fields": [
        {
            "name": "id",
            "type": "Edm.String",
            "key": true,
            "searchable": false,
            "filterable": true,
            "retrievable": true,
            "sortable": false,
            "facetable": false
        },
        {
            "name": "content",
            "type": "Edm.String",
            "searchable": true,
            "filterable": false,
            "retrievable": true,
            "sortable": false,
            "facetable": false,
            "analyzer": "zh-Hant.microsoft"
        },
        {
            "name": "metadata_storage_name",
            "type": "Edm.String",
            "searchable": true,
            "filterable": true,
            "retrievable": true,
            "sortable": true,
            "facetable": true
        },
        {
            "name": "metadata_storage_path",
            "type": "Edm.String",
            "searchable": false,
            "filterable": true,
            "retrievable": true,
            "sortable": false,
            "facetable": false
        },
        {
            "name": "metadata_storage_size",
            "type": "Edm.Int64",
            "searchable": false,
            "filterable": true,
            "retrievable": true,
            "sortable": true,
            "facetable": true
        },
        {
            "name": "metadata_storage_last_modified",
            "type": "Edm.DateTimeOffset",
            "searchable": false,
            "filterable": true,
            "retrievable": true,
            "sortable": true,
            "facetable": true
        },
        {
            "name": "metadata_content_type",
            "type": "Edm.String",
            "searchable": false,
            "filterable": true,
            "retrievable": true,
            "sortable": false,
            "facetable": true
        },
        {
            "name": "pages",
            "type": "Collection(Edm.String)",
            "searchable": true,
            "filterable": false,
            "retrievable": true,
            "sortable": false,
            "facetable": false,
            "analyzer": "zh-Hant.microsoft"
        },
        {
            "name": "keyPhrases",
            "type": "Collection(Edm.String)",
            "searchable": true,
            "filterable": true,
            "retrievable": true,
            "sortable": false,
            "facetable": true
        },
        {
            "name": "persons",
            "type": "Collection(Edm.String)",
            "searchable": true,
            "filterable": true,
            "retrievable": true,
            "sortable": false,
            "facetable": true
        },
        {
            "name": "organizations",
            "type": "Collection(Edm.String)",
            "searchable": true,
            "filterable": true,
            "retrievable": true,
            "sortable": false,
            "facetable": true
        },
        {
            "name": "locations",
            "type": "Collection(Edm.String)",
            "searchable": true,
            "filterable": true,
            "retrievable": true,
            "sortable": false,
            "facetable": true
        },
        {
            "name": "ocrText",
            "type": "Collection(Edm.String)",
            "searchable": true,
            "filterable": false,
            "retrievable": true,
            "sortable": false,
            "facetable": false,
            "analyzer": "zh-Hant.microsoft"
        }
    ],
    "suggesters": [
        {
            "name": "sg",
            "searchMode": "analyzingInfixMatching",
            "sourceFields": ["content", "keyPhrases", "organizations"]
        }
    ],
    "analyzers": [],
    "charFilters": [],
    "tokenizers": [],
    "tokenFilters": [],
    "defaultScoringProfile": null,
    "scoringProfiles": [],
    "corsOptions": {
        "allowedOrigins": ["*"],
        "maxAgeInSeconds": 300
    },
    "semantic": {
        "configurations": [
            {
                "name": "patent-semantic-config",
                "prioritizedFields": {
                    "titleField": {
                        "fieldName": "metadata_storage_name"
                    },
                    "prioritizedContentFields": [
                        {
                            "fieldName": "content"
                        },
                        {
                            "fieldName": "pages"
                        }
                    ],
                    "prioritizedKeywordsFields": [
                        {
                            "fieldName": "keyPhrases"
                        }
                    ]
                }
            }
        ]
    }
}
EOF

curl -X POST \
    "https://$SEARCH_SERVICE_NAME.search.windows.net/indexes?api-version=2023-11-01" \
    -H "Content-Type: application/json" \
    -H "api-key: $SEARCH_API_KEY" \
    -d @index.json

# --- 4. 建立索引器 (Indexer) ---
echo "正在建立索引器..."

cat > indexer.json << EOF
{
    "name": "$INDEXER_NAME",
    "description": "專利文件索引器",
    "dataSourceName": "$DATASOURCE_NAME",
    "targetIndexName": "$PATENT_INDEX_NAME",
    "skillsetName": "$SKILLSET_NAME",
    "schedule": {
        "interval": "PT2H"
    },
    "parameters": {
        "batchSize": 50,
        "maxFailedItems": 10,
        "maxFailedItemsPerBatch": 5,
        "configuration": {
            "dataToExtract": "contentAndMetadata",
            "parsingMode": "default",
            "imageAction": "generateNormalizedImages",
            "allowSkillsetToReadFileData": true
        }
    },
    "fieldMappings": [
        {
            "sourceFieldName": "metadata_storage_path",
            "targetFieldName": "id",
            "mappingFunction": {
                "name": "base64Encode"
            }
        },
        {
            "sourceFieldName": "metadata_storage_name",
            "targetFieldName": "metadata_storage_name"
        },
        {
            "sourceFieldName": "metadata_storage_path",
            "targetFieldName": "metadata_storage_path"
        },
        {
            "sourceFieldName": "metadata_storage_size",
            "targetFieldName": "metadata_storage_size"
        },
        {
            "sourceFieldName": "metadata_storage_last_modified",
            "targetFieldName": "metadata_storage_last_modified"
        },
        {
            "sourceFieldName": "metadata_content_type",
            "targetFieldName": "metadata_content_type"
        }
    ],
    "outputFieldMappings": [
        {
            "sourceFieldName": "/document/content",
            "targetFieldName": "content"
        },
        {
            "sourceFieldName": "/document/pages/*",
            "targetFieldName": "pages"
        },
        {
            "sourceFieldName": "/document/pages/*/keyPhrases/*",
            "targetFieldName": "keyPhrases"
        },
        {
            "sourceFieldName": "/document/pages/*/persons/*",
            "targetFieldName": "persons"
        },
        {
            "sourceFieldName": "/document/pages/*/organizations/*",
            "targetFieldName": "organizations"
        },
        {
            "sourceFieldName": "/document/pages/*/locations/*",
            "targetFieldName": "locations"
        },
        {
            "sourceFieldName": "/document/normalized_images/*/text",
            "targetFieldName": "ocrText"
        }
    ]
}
EOF

curl -X POST \
    "https://$SEARCH_SERVICE_NAME.search.windows.net/indexers?api-version=2023-11-01" \
    -H "Content-Type: application/json" \
    -H "api-key: $SEARCH_API_KEY" \
    -d @indexer.json

# --- 5. 執行索引器 ---
echo "正在執行索引器..."
curl -X POST \
    "https://$SEARCH_SERVICE_NAME.search.windows.net/indexers/$INDEXER_NAME/run?api-version=2023-11-01" \
    -H "api-key: $SEARCH_API_KEY"

# --- 6. 清理暫存檔案 ---
rm -f datasource.json skillset.json index.json indexer.json

# ===========================================
# 配置完成
# ===========================================

echo -e "\n\nAzure AI Search配置完成！"
echo "============================================"
echo "搜尋服務: $SEARCH_SERVICE_NAME"
echo "索引名稱: $PATENT_INDEX_NAME"
echo "資料來源: $DATASOURCE_NAME"
echo "技能集: $SKILLSET_NAME"
echo "索引器: $INDEXER_NAME"
echo "============================================"
echo "索引器已開始執行，請稍後檢查索引狀態。"
echo "您可以在Azure Portal中監控索引進度。"

echo -e "\n檢查索引器狀態的命令："
echo "curl -H \"api-key: $SEARCH_API_KEY\" \"https://$SEARCH_SERVICE_NAME.search.windows.net/indexers/$INDEXER_NAME/status?api-version=2023-11-01\""

echo -e "\n測試搜尋的命令："
echo "curl -H \"api-key: $SEARCH_API_KEY\" \"https://$SEARCH_SERVICE_NAME.search.windows.net/indexes/$PATENT_INDEX_NAME/docs?api-version=2023-11-01&search=*&\$count=true\""
