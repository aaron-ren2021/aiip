"""
RPA自動專利比對機器人 - 後端API系統
主要應用程式入口點
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio
import logging
from datetime import datetime
import uuid

# 導入自定義模組
from models.database import init_db, get_db_session
from models.patent_models import PatentSearchRequest, PatentSearchResult, TaskStatus
from services.patent_search_service import PatentSearchService
from services.rpa_service import RPAService
from services.rag_service import RAGService
from utils.azure_config import AzureConfig
from utils.logger import setup_logger

# 設定日誌
logger = setup_logger(__name__)

# 建立FastAPI應用程式
app = FastAPI(
    title="RPA自動專利比對機器人 API",
    description="整合Azure AI Search、RPA與RAG技術的專利檢索比對系統",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全性設定
security = HTTPBearer()

# 全域變數
azure_config = AzureConfig()
patent_service = PatentSearchService()
rpa_service = RPAService()
rag_service = RAGService()

@app.on_event("startup")
async def startup_event():
    """應用程式啟動時的初始化作業"""
    try:
        logger.info("正在啟動RPA專利比對系統...")
        
        # 初始化資料庫
        await init_db()
        
        # 初始化Azure服務連線
        await azure_config.initialize()
        
        # 初始化各項服務
        await patent_service.initialize()
        await rpa_service.initialize()
        await rag_service.initialize()
        
        logger.info("系統啟動完成")
        
    except Exception as e:
        logger.error(f"系統啟動失敗: {str(e)}")
        # 不要重新拋出異常，讓系統可以繼續運行，但會在健康檢查中反映問題
        pass

@app.on_event("shutdown")
async def shutdown_event():
    """應用程式關閉時的清理作業"""
    logger.info("正在關閉系統...")
    
    # 清理資源
    await patent_service.cleanup()
    await rpa_service.cleanup()
    await rag_service.cleanup()
    
    logger.info("系統已安全關閉")

# API路由定義

@app.get("/")
async def root():
    """根路徑 - 系統狀態檢查"""
    return {
        "message": "RPA自動專利比對機器人系統",
        "status": "運行中",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        # 檢查各項服務狀態
        db_status = await patent_service.check_health()
        azure_status = await azure_config.check_health()
        rpa_status = await rpa_service.check_health()
        rag_status = await rag_service.check_health()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_status,
                "azure_services": azure_status,
                "rpa_service": rpa_status,
                "rag_service": rag_status
            }
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=503, detail="服務不可用")

@app.post("/api/v1/patent/search", response_model=Dict[str, Any])
async def create_patent_search_task(
    request: PatentSearchRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """建立專利檢索任務"""
    try:
        # 驗證請求
        if not request.keywords and not request.patent_number:
            raise HTTPException(
                status_code=400, 
                detail="必須提供關鍵字或專利號碼"
            )
        
        # 建立任務ID
        task_id = str(uuid.uuid4())
        
        # 記錄任務到資料庫
        task_data = {
            "task_id": task_id,
            "request_data": request.dict(),
            "status": TaskStatus.PENDING,
            "created_at": datetime.now(),
            "user_id": credentials.credentials  # 從JWT token中提取
        }
        
        await patent_service.create_task(task_data)
        
        # 背景執行RPA檢索任務
        background_tasks.add_task(
            execute_patent_search_workflow,
            task_id,
            request
        )
        
        logger.info(f"已建立專利檢索任務: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "已接受",
            "message": "專利檢索任務已建立，正在處理中...",
            "estimated_time": "5-15分鐘"
        }
        
    except Exception as e:
        logger.error(f"建立檢索任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/patent/search/{task_id}/status")
async def get_task_status(task_id: str):
    """查詢任務狀態"""
    try:
        task_info = await patent_service.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        return task_info
        
    except Exception as e:
        logger.error(f"查詢任務狀態失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/patent/search/{task_id}/results")
async def get_search_results(task_id: str):
    """取得檢索結果"""
    try:
        results = await patent_service.get_search_results(task_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="結果不存在或任務尚未完成")
        
        return results
        
    except Exception as e:
        logger.error(f"取得檢索結果失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/patent/analyze")
async def analyze_patents(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """使用RAG進行專利分析"""
    try:
        # 驗證輸入
        if "patent_ids" not in request or not request["patent_ids"]:
            raise HTTPException(
                status_code=400,
                detail="必須提供要分析的專利ID清單"
            )
        
        # 執行RAG分析
        analysis_result = await rag_service.analyze_patents(
            patent_ids=request["patent_ids"],
            analysis_type=request.get("analysis_type", "similarity"),
            target_patent=request.get("target_patent")
        )
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"專利分析失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/patent/databases")
async def get_available_databases():
    """取得可用的專利資料庫清單"""
    try:
        databases = await patent_service.get_available_databases()
        return {"databases": databases}
        
    except Exception as e:
        logger.error(f"取得資料庫清單失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks")
async def get_user_tasks(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = 20,
    offset: int = 0
):
    """取得使用者的任務清單"""
    try:
        user_id = credentials.credentials
        tasks = await patent_service.get_user_tasks(user_id, limit, offset)
        
        return {
            "tasks": tasks,
            "total": len(tasks),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"取得任務清單失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 背景任務函數

async def execute_patent_search_workflow(task_id: str, request: PatentSearchRequest):
    """執行完整的專利檢索工作流程"""
    try:
        logger.info(f"開始執行專利檢索工作流程: {task_id}")
        
        # 更新任務狀態為進行中
        await patent_service.update_task_status(task_id, TaskStatus.RUNNING)
        
        # 步驟1: 觸發RPA機器人進行檢索
        rpa_results = await rpa_service.execute_patent_search(
            task_id=task_id,
            databases=request.databases,
            keywords=request.keywords,
            patent_number=request.patent_number,
            search_options=request.search_options
        )
        
        # 步驟2: 處理檢索到的專利文件
        processed_patents = await patent_service.process_search_results(
            task_id, rpa_results
        )
        
        # 步驟3: 建立向量索引（用於RAG）
        await rag_service.index_patents(processed_patents)
        
        # 步驟4: 執行初步分析
        if request.enable_analysis:
            analysis_results = await rag_service.analyze_patents(
                patent_ids=[p["id"] for p in processed_patents],
                analysis_type="similarity"
            )
            
            # 將分析結果併入最終結果
            for patent in processed_patents:
                patent_analysis = next(
                    (a for a in analysis_results if a["patent_id"] == patent["id"]), 
                    None
                )
                if patent_analysis:
                    patent["analysis"] = patent_analysis
        
        # 步驟5: 儲存最終結果
        await patent_service.save_search_results(task_id, processed_patents)
        
        # 更新任務狀態為完成
        await patent_service.update_task_status(task_id, TaskStatus.COMPLETED)
        
        logger.info(f"專利檢索工作流程完成: {task_id}")
        
    except Exception as e:
        logger.error(f"專利檢索工作流程失敗: {task_id}, 錯誤: {str(e)}")
        
        # 更新任務狀態為失敗
        await patent_service.update_task_status(
            task_id, 
            TaskStatus.FAILED, 
            error_message=str(e)
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
