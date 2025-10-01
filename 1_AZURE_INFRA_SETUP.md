# RPA自動專利比對機器人系統 - Azure基礎設施準備指南

本文將指導您完成在Microsoft Azure上部署「RPA自動專利比對機器人系統」所需的基礎設施準備工作。我們將使用Azure CLI腳本自動化大部分資源的建立過程，以確保一致性並減少手動錯誤。

## 總覽

此階段的目標是建立一個穩固、安全且可擴展的雲端基礎設施，以支援本系統的各個組件，包括後端API、前端應用、RPA機器人、資料庫、快取以及AI服務。

### 建立的資源

我們將透過自動化腳本建立以下Azure資源：

| 資源類型 | 用途 | SKU (範例) |
| :--- | :--- | :--- |
| **資源群組 (Resource Group)** | 集中管理所有相關資源 | N/A |
| **容器註冊表 (ACR)** | 儲存和管理Docker映像檔 | `Standard` |
| **Kubernetes服務 (AKS)** | 容器協調與管理 | `Standard_DS2_v2` (3節點) |
| **PostgreSQL資料庫** | 主要的結構化資料儲存 | `B_Gen5_2` |
| **Redis快取** | 快取常用資料以提升效能 | `Basic C0` (250MB) |
| **AI Search** | 提供強大的專利檢索與RAG能力 | `basic` |
| **OpenAI服務** | 提供大型語言模型能力 | `S0` |
| **Blob儲存體** | 儲存專利文件、報告等非結構化資料 | `Standard_LRS` |
| **Key Vault** | 安全地儲存和管理密鑰、密碼和憑證 | N/A |

## 前置準備

在執行腳本之前，請確保您已完成以下準備工作：

1.  **安裝 Azure CLI**：請參考 [Azure CLI 安裝指南](https://docs.microsoft.com/cli/azure/install-azure-cli) 完成安裝。
2.  **登入 Azure 帳戶**：開啟您的終端機或命令提示字元，執行 `az login` 並依照指示完成登入。
3.  **確認訂用帳戶**：如果您有多個Azure訂用帳戶，請使用 `az account set --subscription "<您的訂用帳戶名稱或ID>"` 設定要使用的訂用帳戶。
4.  **下載專案檔案**：確保您已取得完整的 `patent-rpa-system` 專案檔案，特別是 `azure-config/scripts/provision_azure_infra.sh` 腳本。

## 自動化部署步驟

我們強烈建議使用提供的Shell腳本來自動建立所有必要的Azure資源。這能確保所有資源都按照最佳實踐進行配置。

### 1. 檢視與修改腳本變數

開啟 `azure-config/scripts/provision_azure_infra.sh` 腳本。在檔案的開頭，您會看到一個配置變數區塊。請根據您的需求和命名慣例修改這些變數。

> **重要提示**：
> - `ACR_NAME`, `POSTGRES_SERVER_NAME`, `REDIS_CACHE_NAME`, `SEARCH_SERVICE_NAME`, `OPENAI_SERVICE_NAME`, `STORAGE_ACCOUNT_NAME`, `KEY_VAULT_NAME` 都必須是 **全域唯一** 的。腳本預設會附加隨機數，但您也可以自行指定。
> - **請務必修改 `POSTGRES_ADMIN_PASSWORD`** 為一個高強度的安全密碼。這非常重要！

```bash
# 資源群組
RESOURCE_GROUP="PatentRPASystemRG"
LOCATION="eastus" # 建議選擇離您最近的Azure區域

# ... 其他變數 ...

# Azure Database for PostgreSQL
POSTGRES_ADMIN_PASSWORD="your_secure_password_here_P@ssw0rd123!" # 請務必更換為高強度密碼

# ... 其他變數 ...
```

### 2. 賦予腳本執行權限

在終端機中，導覽至專案根目錄，並執行以下命令，賦予腳本執行權限：

```bash
chmod +x azure-config/scripts/provision_azure_infra.sh
```

### 3. 執行部署腳本

執行以下命令以開始建立Azure資源。整個過程可能需要 **15到30分鐘**，請耐心等候。

```bash
./azure-config/scripts/provision_azure_infra.sh
```

腳本會依序建立所有資源，並在過程中顯示進度。如果遇到任何錯誤，腳本會停止執行，您可以根據錯誤訊息進行排查。

### 4. 確認部署結果

腳本執行成功後，您會在終端機看到所有已建立資源的摘要資訊。您也可以登入 [Azure Portal](https://portal.azure.com/)，找到名為 `PatentRPASystemRG` 的資源群組，確認所有資源都已成功建立。

> **安全性最佳實踐**：
> 腳本會自動將所有重要的密鑰和連接字串（例如資料庫密碼、ACR密碼、儲存體連接字串等）儲存在新建立的 **Azure Key Vault** 中。在後續的應用程式部署階段，我們會配置應用程式從Key Vault中安全地讀取這些敏感資訊，而不是將它們硬編碼在設定檔中。

## 下一步

完成基礎設施的準備後，您就可以進入下一個階段：**Azure AI Search與認知服務整合**。在這個階段，我們將設定AI Search的索引、索引器，並與Blob儲存體和OpenAI服務進行整合，以實現強大的RPA知識管理與檢索能力。

---
*本文件由 Manus AI 自動生成。*
