"""
專利檢索服務模組
負責協調RPA機器人執行專利檢索任務
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from models.patent_models import (
    PatentSearchRequest, PatentInfo, TaskStatus, PatentDatabase,
    RPATaskRequest, RPATaskResult
)
from models.database import PatentRepository, TaskRepository, db_manager
from utils.azure_config import AzureConfig

logger = logging.getLogger(__name__)

class PatentSearchService:
    """專利檢索服務"""
    
    def __init__(self):
        self.azure_config = AzureConfig()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """初始化服務"""
        try:
            logger.info("正在初始化專利檢索服務...")
            # 這裡可以加入服務初始化邏輯
            logger.info("專利檢索服務初始化完成")
        except Exception as e:
            logger.error(f"專利檢索服務初始化失敗: {str(e)}")
            raise
    
    async def cleanup(self):
        """清理資源"""
        logger.info("正在清理專利檢索服務資源...")
        # 清理活躍任務
        self.active_tasks.clear()
        logger.info("專利檢索服務資源清理完成")
    
    async def check_health(self) -> str:
        """健康檢查"""
        try:
            # 檢查資料庫連線
            async with db_manager.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            
            return "healthy"
        except Exception as e:
            logger.error(f"專利檢索服務健康檢查失敗: {str(e)}")
            return "unhealthy"
    
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """建立檢索任務"""
        try:
            task_id = await TaskRepository.create_task(task_data)
            
            # 記錄活躍任務
            self.active_tasks[task_id] = {
                "status": TaskStatus.PENDING,
                "created_at": datetime.now(),
                "progress": 0
            }
            
            logger.info(f"已建立檢索任務: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"建立檢索任務失敗: {str(e)}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """取得任務狀態"""
        try:
            task_info = await TaskRepository.get_task_by_id(task_id)
            
            if not task_info:
                return None
            
            # 合併活躍任務資訊
            if task_id in self.active_tasks:
                task_info.update(self.active_tasks[task_id])
            
            return {
                "task_id": task_info["task_id"],
                "status": task_info["status"],
                "progress": task_info.get("progress", 0),
                "message": task_info.get("message"),
                "error_message": task_info.get("error_message"),
                "created_at": task_info["created_at"],
                "updated_at": task_info["updated_at"],
                "completed_at": task_info.get("completed_at")
            }
            
        except Exception as e:
            logger.error(f"取得任務狀態失敗: {str(e)}")
            raise
    
    async def update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus, 
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """更新任務狀態"""
        try:
            await TaskRepository.update_task_status(
                task_id, status.value, progress, message, error_message
            )
            
            # 更新活躍任務記錄
            if task_id in self.active_tasks:
                self.active_tasks[task_id].update({
                    "status": status,
                    "progress": progress or self.active_tasks[task_id].get("progress", 0),
                    "updated_at": datetime.now()
                })
                
                # 如果任務完成或失敗，從活躍任務中移除
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    del self.active_tasks[task_id]
            
            logger.info(f"任務狀態已更新: {task_id} -> {status.value}")
            
        except Exception as e:
            logger.error(f"更新任務狀態失敗: {str(e)}")
            raise
    
    async def get_search_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """取得檢索結果"""
        try:
            task_info = await TaskRepository.get_task_by_id(task_id)
            
            if not task_info or task_info["status"] != TaskStatus.COMPLETED.value:
                return None
            
            # 解析結果資料
            result_data = task_info.get("result_data")
            if result_data:
                if isinstance(result_data, str):
                    result_data = json.loads(result_data)
                return result_data
            
            return None
            
        except Exception as e:
            logger.error(f"取得檢索結果失敗: {str(e)}")
            raise
    
    async def save_search_results(self, task_id: str, results: List[Dict[str, Any]]):
        """儲存檢索結果"""
        try:
            # 儲存專利資料到資料庫
            saved_patents = []
            
            for patent_data in results:
                try:
                    # 檢查專利是否已存在
                    existing_patent = await PatentRepository.get_patent_by_id(
                        patent_data["patent_id"]
                    )
                    
                    if not existing_patent:
                        # 建立新專利記錄
                        await PatentRepository.create_patent(patent_data)
                        logger.info(f"已儲存專利: {patent_data['patent_id']}")
                    
                    saved_patents.append(patent_data)
                    
                except Exception as e:
                    logger.error(f"儲存專利失敗: {patent_data.get('patent_id', 'unknown')}, 錯誤: {str(e)}")
                    continue
            
            # 更新任務結果
            result_summary = {
                "total_found": len(saved_patents),
                "patents": saved_patents,
                "search_summary": {
                    "databases_searched": list(set([p.get("source_database") for p in saved_patents])),
                    "search_completed_at": datetime.now().isoformat()
                }
            }
            
            async with db_manager.get_connection() as conn:
                await conn.execute(
                    "UPDATE tasks SET result_data = $1 WHERE task_id = $2",
                    json.dumps(result_summary, default=str),
                    task_id
                )
            
            logger.info(f"已儲存檢索結果: {task_id}, 共 {len(saved_patents)} 筆專利")
            
        except Exception as e:
            logger.error(f"儲存檢索結果失敗: {str(e)}")
            raise
    
    async def process_search_results(
        self, 
        task_id: str, 
        rpa_results: List[RPATaskResult]
    ) -> List[Dict[str, Any]]:
        """處理RPA檢索結果"""
        try:
            processed_patents = []
            
            for rpa_result in rpa_results:
                if rpa_result.status != "completed":
                    logger.warning(f"RPA任務未完成: {rpa_result.task_id}")
                    continue
                
                # 處理下載的檔案
                for file_path in rpa_result.downloaded_files:
                    try:
                        # 解析專利文件
                        patent_data = await self._parse_patent_file(file_path)
                        
                        if patent_data:
                            # 生成唯一ID
                            patent_data["patent_id"] = str(uuid.uuid4())
                            patent_data["task_id"] = task_id
                            processed_patents.append(patent_data)
                            
                    except Exception as e:
                        logger.error(f"解析專利文件失敗: {file_path}, 錯誤: {str(e)}")
                        continue
            
            logger.info(f"已處理 {len(processed_patents)} 筆專利資料")
            return processed_patents
            
        except Exception as e:
            logger.error(f"處理檢索結果失敗: {str(e)}")
            raise
    
    async def _parse_patent_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """解析專利文件"""
        try:
            # 這裡應該實作專利文件解析邏輯
            # 支援PDF、HTML、XML等格式
            
            # 暫時返回模擬資料
            return {
                "patent_number": f"TW{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": "模擬專利標題",
                "abstract": "模擬專利摘要",
                "inventors": ["發明人1", "發明人2"],
                "applicants": ["申請人1"],
                "application_date": datetime.now(),
                "publication_date": datetime.now(),
                "ipc_classes": ["G06F"],
                "claims": "模擬申請專利範圍",
                "description": "模擬說明書內容",
                "images": [],
                "source_database": "twpat",
                "source_url": f"file://{file_path}"
            }
            
        except Exception as e:
            logger.error(f"解析專利文件失敗: {file_path}, 錯誤: {str(e)}")
            return None
    
    async def get_available_databases(self) -> List[Dict[str, Any]]:
        """取得可用的專利資料庫清單"""
        try:
            databases = []
            
            for db in PatentDatabase:
                db_info = {
                    "code": db.value,
                    "name": self._get_database_name(db),
                    "description": self._get_database_description(db),
                    "status": "available",  # 實際應該檢查資料庫狀態
                    "features": self._get_database_features(db)
                }
                databases.append(db_info)
            
            return databases
            
        except Exception as e:
            logger.error(f"取得資料庫清單失敗: {str(e)}")
            raise
    
    def _get_database_name(self, db: PatentDatabase) -> str:
        """取得資料庫名稱"""
        names = {
            PatentDatabase.TWPAT: "中華民國專利檢索系統",
            PatentDatabase.USPTO: "美國專利商標局",
            PatentDatabase.EPO: "歐洲專利局",
            PatentDatabase.WIPO: "世界智慧財產權組織",
            PatentDatabase.JPO: "日本特許廳",
            PatentDatabase.CNIPA: "中國國家知識產權局",
            PatentDatabase.KIPO: "韓國特許廳"
        }
        return names.get(db, db.value)
    
    def _get_database_description(self, db: PatentDatabase) -> str:
        """取得資料庫描述"""
        descriptions = {
            PatentDatabase.TWPAT: "台灣地區專利檢索系統，包含發明、新型、設計專利",
            PatentDatabase.USPTO: "美國專利商標局官方資料庫，涵蓋美國所有專利",
            PatentDatabase.EPO: "歐洲專利局資料庫，涵蓋歐洲專利申請案",
            PatentDatabase.WIPO: "世界智慧財產權組織全球專利資料庫",
            PatentDatabase.JPO: "日本特許廳專利資料庫",
            PatentDatabase.CNIPA: "中國大陸專利檢索系統",
            PatentDatabase.KIPO: "韓國特許廳專利資料庫"
        }
        return descriptions.get(db, "專利資料庫")
    
    def _get_database_features(self, db: PatentDatabase) -> List[str]:
        """取得資料庫功能特色"""
        features = {
            PatentDatabase.TWPAT: ["中文檢索", "圖片下載", "全文檢索"],
            PatentDatabase.USPTO: ["英文檢索", "PDF下載", "圖式檢索", "引用分析"],
            PatentDatabase.EPO: ["多語言檢索", "機器翻譯", "分類檢索"],
            PatentDatabase.WIPO: ["PCT檢索", "多語言支援", "國際分類"],
            PatentDatabase.JPO: ["日文檢索", "機器翻譯", "圖式檢索"],
            PatentDatabase.CNIPA: ["中文檢索", "簡繁轉換", "分類檢索"],
            PatentDatabase.KIPO: ["韓文檢索", "英文摘要", "分類檢索"]
        }
        return features.get(db, ["基本檢索"])
    
    async def get_user_tasks(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """取得使用者的任務清單"""
        try:
            tasks = await TaskRepository.get_user_tasks(user_id, limit, offset)
            
            # 格式化任務資料
            formatted_tasks = []
            for task in tasks:
                formatted_task = {
                    "task_id": task["task_id"],
                    "status": task["status"],
                    "progress": task.get("progress", 0),
                    "message": task.get("message"),
                    "created_at": task["created_at"],
                    "updated_at": task["updated_at"],
                    "completed_at": task.get("completed_at")
                }
                
                # 解析請求資料
                if task.get("request_data"):
                    try:
                        request_data = task["request_data"]
                        if isinstance(request_data, str):
                            request_data = json.loads(request_data)
                        
                        formatted_task["request_summary"] = {
                            "keywords": request_data.get("keywords"),
                            "patent_number": request_data.get("patent_number"),
                            "databases": request_data.get("databases", [])
                        }
                    except Exception as e:
                        logger.error(f"解析請求資料失敗: {str(e)}")
                
                formatted_tasks.append(formatted_task)
            
            return formatted_tasks
            
        except Exception as e:
            logger.error(f"取得使用者任務清單失敗: {str(e)}")
            raise
