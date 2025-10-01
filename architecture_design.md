# RPA自動專利比對機器人：系統架構與技術選型

## 1. 專案目標與總覽

本專案旨在建立一個功能強大、可擴展且安全的「RPA自動專利比對機器人」系統。此系統將利用先進的雲端服務、人工智慧（AI）與機器人流程自動化（RPA）技術，實現對全球專利資料庫的自動化檢索、比對與分析，最終生成詳盡的侵權風險評估報告。

根據您的需求，系統將部署於 **Microsoft Azure** 雲端平台，並整合 **Azure AI Search** 作為RAG（檢索增強生成）知識庫的核心，同時與 **Automation Anywhere** RPA平台進行深度整合。

## 2. 系統架構設計

我們將採用基於微服務（Microservices）的現代雲原生架構，以確保系統的模組化、彈性與可維護性。所有服務將被容器化（Docker），並透過Azure的容器服務進行託管與協調。

以下是系統的核心組件與其互動關係：

```mermaid
graph TD
    subgraph 用戶端 (Client)
        A[前端應用程式 (React)]
    end

    subgraph Azure 雲端平台
        B[API Gateway (Azure API Management)]
        C[後端API服務 (FastAPI on Azure Container Apps)]
        D[任務佇列 (Azure Service Bus)]
        E[RAG智能分析引擎]
        F[結構化資料庫 (Azure PostgreSQL)]
        G[向量/索引資料庫 (Azure AI Search)]
        H[檔案儲存 (Azure Blob Storage)]
        I[CI/CD (Azure DevOps)]
    end

    subgraph RPA 平台
        J[Automation Anywhere Control Room]
        K[RPA 機器人 (Bot Agent)]
    end

    subgraph 外部資料來源
        L[專利資料庫 (TWPAT, USPTO, etc.)]
    end

    A -->|RESTful API| B
    B --> C
    C --> D
    C --> F
    C --> E
    C --> H
    E --> G
    E --> OpenAI[Azure OpenAI Service]
    D --> J
    J --> K
    K --> L
    K --> H
    K --> C
```

### 資料流程說明：

1.  **使用者互動**：使用者透過前端介面提交專利比對需求。
2.  **API請求**：前端應用程式呼叫後端的API Gateway。
3.  **任務建立**：後端API服務接收請求，將任務資訊存入結構化資料庫（PostgreSQL），並將檢索指令發布到任務佇列（Azure Service Bus）。
4.  **RPA觸發**：Automation Anywhere Control Room監聽任務佇列，一旦有新任務，便指派RPA機器人執行。
5.  **專利檢索**：RPA機器人根據指令，自動登入並爬取指定的內外部專利資料庫，下載相關專利文件（PDF、圖片等）。
6.  **文件儲存與前處理**：機器人將原始文件儲存至Azure Blob Storage。後端服務可觸發Azure Functions進行文件的OCR辨識與文字擷取。
7.  **RAG分析**：
    *   擷取出的文本被送往Azure OpenAI Service進行向量化（Embeddings）。
    *   文本與其向量表示被存入Azure AI Search，建立可供檢索的知識索引。
    *   當需要進行比對分析時，RAG引擎會從Azure AI Search中檢索最相關的專利文件，並結合大型語言模型（LLM）生成技術特徵分析、相似度比對與侵權風險評估。
8.  **結果回傳**：分析結果被存回結構化資料庫，並透過後端API呈現給前端使用者。

## 3. 技術選型 (Technology Stack)

為了實現上述架構，我們將採用以下技術堆疊，這與您提供的Checklist中的選項一致，並針對Azure環境進行了最佳化。

| 組件類別 | 技術選型 | 選擇理由 |
| :--- | :--- | :--- |
| **雲端平台** | **Microsoft Azure** | 根據使用者明確指定，並能與M365、Power Platform無縫整合。 |
| **容器化** | **Docker** | 實現環境標準化，簡化開發與部署流程，是雲原生應用的基石。 |
| **容器託管** | **Azure Container Apps** | 提供無伺服器的容器運行環境，具備自動擴展、負載平衡與簡易的微服務管理能力。 |
| **後端框架** | **FastAPI (Python)** | 高效能的非同步Web框架，適合快速開發API，且Python在AI/ML領域擁有最豐富的生態系。 |
| **前端框架** | **React** | 成熟、穩定且社群龐大的前端函式庫，可建構複雜且高效的使用者介面。 |
| **RPA平台** | **Automation Anywhere** | 根據使用者明確指定，提供強大的企業級自動化能力。 |
| **RAG框架** | **LangChain / LlamaIndex** | 兩者均為優秀的LLM應用開發框架，我們將主要使用LangChain來串連RAG流程。 |
| **向量資料庫** | **Azure AI Search** | 根據使用者明確指定，原生整合向量檢索與混合式搜尋，是Azure上實現RAG的首選。 |
| **結構化資料庫**| **Azure Database for PostgreSQL** | 成熟的開源關聯式資料庫，功能強大、穩定可靠，並由Azure提供全託管服務。 |
| **任務佇列** | **Azure Service Bus** | 可靠的企業級訊息代理服務，用於解耦後端服務與RPA機器人，確保任務不遺失。 |
| **檔案儲存** | **Azure Blob Storage** | 高度可擴展、安全且成本低廉的物件儲存服務，適合存放專利文件、圖片等非結構化資料。 |
| **CI/CD** | **Azure DevOps / GitHub Actions** | 兩者均能與Azure深度整合，實現從程式碼提交到自動化部署的完整流程。 |
| **API閘道** | **Azure API Management** | 集中管理API的安全性、監控、快取與流量控制，是微服務架構的重要組件。 |

---

接下來，我將根據此架構設計，開始進行 **核心後端API系統的開發**。
