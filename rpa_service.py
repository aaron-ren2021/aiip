"""
RPA服務模組
整合Automation Anywhere，執行專利檢索自動化任務
"""

import asyncio
import logging
import json
import aiohttp
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import os

from models.patent_models import (
    RPATaskRequest, RPATaskResult, PatentDatabase, SearchOptions
)
from utils.azure_config import AzureConfig

logger = logging.getLogger(__name__)

class RPAService:
    """RPA服務管理器"""
    
    def __init__(self):
        self.azure_config = AzureConfig()
        self.aa_config = self._load_aa_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # RPA機器人配置
        self.robot_configs = {
            "twpat_searcher": {
                "name": "TWPAT專利檢索機器人",
                "bot_id": "twpat-search-bot-v1",
                "capabilities": ["關鍵字檢索", "專利號檢索", "PDF下載", "圖片擷取"],
                "target_database": PatentDatabase.TWPAT
            },
            "uspto_searcher": {
                "name": "USPTO專利檢索機器人", 
                "bot_id": "uspto-search-bot-v1",
                "capabilities": ["關鍵字檢索", "專利號檢索", "PDF下載", "圖式檢索"],
                "target_database": PatentDatabase.USPTO
            },
            "epo_searcher": {
                "name": "EPO專利檢索機器人",
                "bot_id": "epo-search-bot-v1", 
                "capabilities": ["關鍵字檢索", "多語言檢索", "PDF下載"],
                "target_database": PatentDatabase.EPO
            },
            "wipo_searcher": {
                "name": "WIPO專利檢索機器人",
                "bot_id": "wipo-search-bot-v1",
                "capabilities": ["PCT檢索", "關鍵字檢索", "PDF下載"],
                "target_database": PatentDatabase.WIPO
            },
            "multi_db_searcher": {
                "name": "多資料庫檢索機器人",
                "bot_id": "multi-db-search-bot-v1",
                "capabilities": ["並行檢索", "結果合併", "去重處理"],
                "target_database": None  # 支援多個資料庫
            }
        }
        
        # 任務佇列
        self.task_queue: List[RPATaskRequest] = []
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
    
    def _load_aa_config(self) -> Dict[str, str]:
        """載入Automation Anywhere配置"""
        return {
            "control_room_url": os.getenv("AA_CONTROL_ROOM_URL", ""),
            "username": os.getenv("AA_USERNAME", ""),
            "password": os.getenv("AA_PASSWORD", ""),
            "api_key": os.getenv("AA_API_KEY", ""),
            "workspace_id": os.getenv("AA_WORKSPACE_ID", ""),
            "pool_id": os.getenv("AA_POOL_ID", "")
        }
    
    async def initialize(self):
        """初始化RPA服務"""
        try:
            logger.info("正在初始化RPA服務...")
            
            # 建立HTTP會話
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)  # 5分鐘超時
            )
            
            # 驗證Automation Anywhere連線
            await self._authenticate()
            
            # 檢查機器人狀態
            await self._check_robots_status()
            
            logger.info("RPA服務初始化完成")
            
        except Exception as e:
            logger.error(f"RPA服務初始化失敗: {str(e)}")
            raise
    
    async def cleanup(self):
        """清理資源"""
        logger.info("正在清理RPA服務資源...")
        
        # 取消所有活躍任務
        for task_id in list(self.active_tasks.keys()):
            try:
                await self._cancel_task(task_id)
            except Exception as e:
                logger.error(f"取消任務失敗: {task_id}, 錯誤: {str(e)}")
        
        # 關閉HTTP會話
        if self.session:
            await self.session.close()
        
        logger.info("RPA服務資源清理完成")
    
    async def check_health(self) -> str:
        """健康檢查"""
        try:
            # 檢查Control Room連線
            if not await self._ping_control_room():
                return "unhealthy"
            
            # 檢查認證狀態
            if not await self._check_authentication():
                return "unhealthy"
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"RPA服務健康檢查失敗: {str(e)}")
            return "unhealthy"
    
    async def _authenticate(self):
        """向Automation Anywhere進行身份驗證"""
        try:
            if not self.aa_config["control_room_url"]:
                logger.warning("Automation Anywhere配置不完整，跳過認證")
                return
            
            auth_url = f"{self.aa_config['control_room_url']}/v1/authentication"
            
            # 準備認證資料
            if self.aa_config["api_key"]:
                # 使用API Key認證
                headers = {
                    "X-Authorization": self.aa_config["api_key"],
                    "Content-Type": "application/json"
                }
                auth_data = {}
            else:
                # 使用使用者名稱/密碼認證
                auth_data = {
                    "username": self.aa_config["username"],
                    "password": self.aa_config["password"]
                }
                headers = {"Content-Type": "application/json"}
            
            async with self.session.post(auth_url, json=auth_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("token")
                    
                    # 設定token過期時間（通常24小時）
                    self.token_expires_at = datetime.now() + timedelta(hours=23)
                    
                    logger.info("Automation Anywhere認證成功")
                else:
                    error_text = await response.text()
                    raise Exception(f"認證失敗: {response.status}, {error_text}")
            
        except Exception as e:
            logger.error(f"Automation Anywhere認證失敗: {str(e)}")
            raise
    
    async def _check_authentication(self) -> bool:
        """檢查認證狀態"""
        try:
            if not self.auth_token:
                return False
            
            if self.token_expires_at and datetime.now() >= self.token_expires_at:
                # Token已過期，重新認證
                await self._authenticate()
            
            return bool(self.auth_token)
            
        except Exception as e:
            logger.error(f"檢查認證狀態失敗: {str(e)}")
            return False
    
    async def _ping_control_room(self) -> bool:
        """檢查Control Room連線"""
        try:
            if not self.aa_config["control_room_url"]:
                return False
            
            ping_url = f"{self.aa_config['control_room_url']}/v1/health"
            
            async with self.session.get(ping_url) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Control Room連線檢查失敗: {str(e)}")
            return False
    
    async def _check_robots_status(self):
        """檢查機器人狀態"""
        try:
            if not await self._check_authentication():
                logger.warning("未認證，跳過機器人狀態檢查")
                return
            
            bots_url = f"{self.aa_config['control_room_url']}/v1/repository/workspaces/{self.aa_config['workspace_id']}/files/list"
            
            headers = {
                "X-Authorization": self.auth_token,
                "Content-Type": "application/json"
            }
            
            async with self.session.get(bots_url, headers=headers) as response:
                if response.status == 200:
                    bots_data = await response.json()
                    logger.info(f"找到 {len(bots_data.get('list', []))} 個可用的機器人")
                else:
                    logger.warning(f"無法取得機器人清單: {response.status}")
            
        except Exception as e:
            logger.error(f"檢查機器人狀態失敗: {str(e)}")
    
    async def execute_patent_search(
        self,
        task_id: str,
        databases: List[PatentDatabase],
        keywords: Optional[List[str]] = None,
        patent_number: Optional[str] = None,
        search_options: Optional[SearchOptions] = None
    ) -> List[RPATaskResult]:
        """執行專利檢索任務"""
        try:
            logger.info(f"開始執行專利檢索任務: {task_id}")
            
            results = []
            
            # 為每個資料庫建立RPA任務
            for database in databases:
                try:
                    # 選擇適當的機器人
                    robot_config = self._select_robot_for_database(database)
                    
                    if not robot_config:
                        logger.warning(f"找不到適合的機器人處理資料庫: {database}")
                        continue
                    
                    # 建立RPA任務請求
                    rpa_request = RPATaskRequest(
                        task_id=f"{task_id}_{database.value}",
                        robot_type=robot_config["bot_id"],
                        target_database=database,
                        search_parameters={
                            "keywords": keywords,
                            "patent_number": patent_number,
                            "search_options": search_options.dict() if search_options else {}
                        }
                    )
                    
                    # 執行RPA任務
                    rpa_result = await self._execute_rpa_task(rpa_request)
                    results.append(rpa_result)
                    
                except Exception as e:
                    logger.error(f"執行資料庫檢索失敗: {database}, 錯誤: {str(e)}")
                    
                    # 建立失敗結果
                    failed_result = RPATaskResult(
                        task_id=f"{task_id}_{database.value}",
                        robot_id="unknown",
                        status="failed",
                        results_count=0,
                        downloaded_files=[],
                        execution_log=[f"執行失敗: {str(e)}"],
                        error_details=str(e),
                        execution_time=0,
                        completed_at=datetime.now()
                    )
                    results.append(failed_result)
                    continue
            
            logger.info(f"專利檢索任務完成: {task_id}, 共 {len(results)} 個結果")
            return results
            
        except Exception as e:
            logger.error(f"執行專利檢索任務失敗: {str(e)}")
            raise
    
    def _select_robot_for_database(self, database: PatentDatabase) -> Optional[Dict[str, Any]]:
        """為資料庫選擇適當的機器人"""
        for robot_id, config in self.robot_configs.items():
            if config["target_database"] == database:
                return config
        
        # 如果沒有專用機器人，使用多資料庫機器人
        return self.robot_configs.get("multi_db_searcher")
    
    async def _execute_rpa_task(self, request: RPATaskRequest) -> RPATaskResult:
        """執行單一RPA任務"""
        try:
            start_time = datetime.now()
            
            # 記錄活躍任務
            self.active_tasks[request.task_id] = {
                "request": request,
                "start_time": start_time,
                "status": "running"
            }
            
            # 準備機器人執行參數
            bot_execution_params = {
                "fileId": request.robot_type,
                "runAsUserIds": [],
                "poolIds": [self.aa_config["pool_id"]] if self.aa_config["pool_id"] else [],
                "overrideDefaultDevice": False,
                "callbackInfo": {
                    "url": "",  # 可以設定回調URL
                    "headers": {}
                },
                "botInput": {
                    "taskId": request.task_id,
                    "targetDatabase": request.target_database.value,
                    "searchParameters": request.search_parameters,
                    "options": request.options
                }
            }
            
            # 提交機器人執行請求
            execution_id = await self._submit_bot_execution(bot_execution_params)
            
            if not execution_id:
                raise Exception("無法提交機器人執行請求")
            
            # 等待執行完成
            execution_result = await self._wait_for_execution_completion(execution_id)
            
            # 處理執行結果
            result = await self._process_execution_result(
                request, execution_id, execution_result, start_time
            )
            
            # 從活躍任務中移除
            if request.task_id in self.active_tasks:
                del self.active_tasks[request.task_id]
            
            return result
            
        except Exception as e:
            logger.error(f"執行RPA任務失敗: {request.task_id}, 錯誤: {str(e)}")
            
            # 從活躍任務中移除
            if request.task_id in self.active_tasks:
                del self.active_tasks[request.task_id]
            
            # 返回失敗結果
            return RPATaskResult(
                task_id=request.task_id,
                robot_id=request.robot_type,
                status="failed",
                results_count=0,
                downloaded_files=[],
                execution_log=[f"執行失敗: {str(e)}"],
                error_details=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                completed_at=datetime.now()
            )
    
    async def _submit_bot_execution(self, execution_params: Dict[str, Any]) -> Optional[str]:
        """提交機器人執行請求"""
        try:
            if not await self._check_authentication():
                raise Exception("未認證")
            
            execution_url = f"{self.aa_config['control_room_url']}/v3/activity/orchestrator/execution"
            
            headers = {
                "X-Authorization": self.auth_token,
                "Content-Type": "application/json"
            }
            
            async with self.session.post(execution_url, json=execution_params, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    execution_id = result.get("deploymentId")
                    logger.info(f"機器人執行請求已提交: {execution_id}")
                    return execution_id
                else:
                    error_text = await response.text()
                    logger.error(f"提交機器人執行請求失敗: {response.status}, {error_text}")
                    return None
            
        except Exception as e:
            logger.error(f"提交機器人執行請求失敗: {str(e)}")
            return None
    
    async def _wait_for_execution_completion(
        self, 
        execution_id: str, 
        max_wait_time: int = 1800  # 30分鐘
    ) -> Dict[str, Any]:
        """等待機器人執行完成"""
        try:
            start_time = datetime.now()
            
            while (datetime.now() - start_time).total_seconds() < max_wait_time:
                # 查詢執行狀態
                status_result = await self._get_execution_status(execution_id)
                
                if not status_result:
                    await asyncio.sleep(10)
                    continue
                
                status = status_result.get("status", "").lower()
                
                if status in ["completed", "success"]:
                    logger.info(f"機器人執行完成: {execution_id}")
                    return status_result
                elif status in ["failed", "error", "cancelled"]:
                    logger.error(f"機器人執行失敗: {execution_id}, 狀態: {status}")
                    return status_result
                elif status in ["running", "in_progress", "queued"]:
                    # 繼續等待
                    await asyncio.sleep(30)  # 每30秒檢查一次
                    continue
                else:
                    logger.warning(f"未知的執行狀態: {status}")
                    await asyncio.sleep(30)
            
            # 超時
            logger.error(f"機器人執行超時: {execution_id}")
            return {"status": "timeout", "error": "執行超時"}
            
        except Exception as e:
            logger.error(f"等待機器人執行完成失敗: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """取得機器人執行狀態"""
        try:
            if not await self._check_authentication():
                return None
            
            status_url = f"{self.aa_config['control_room_url']}/v3/activity/orchestrator/execution/{execution_id}"
            
            headers = {
                "X-Authorization": self.auth_token,
                "Content-Type": "application/json"
            }
            
            async with self.session.get(status_url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"取得執行狀態失敗: {response.status}")
                    return None
            
        except Exception as e:
            logger.error(f"取得執行狀態失敗: {str(e)}")
            return None
    
    async def _process_execution_result(
        self,
        request: RPATaskRequest,
        execution_id: str,
        execution_result: Dict[str, Any],
        start_time: datetime
    ) -> RPATaskResult:
        """處理機器人執行結果"""
        try:
            status = execution_result.get("status", "unknown").lower()
            
            # 取得執行日誌
            execution_log = await self._get_execution_logs(execution_id)
            
            # 取得下載的檔案清單
            downloaded_files = await self._get_downloaded_files(execution_id)
            
            # 計算執行時間
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 建立結果物件
            result = RPATaskResult(
                task_id=request.task_id,
                robot_id=request.robot_type,
                status="completed" if status in ["completed", "success"] else "failed",
                results_count=len(downloaded_files),
                downloaded_files=downloaded_files,
                execution_log=execution_log,
                error_details=execution_result.get("error") if status == "failed" else None,
                execution_time=execution_time,
                completed_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"處理執行結果失敗: {str(e)}")
            
            return RPATaskResult(
                task_id=request.task_id,
                robot_id=request.robot_type,
                status="failed",
                results_count=0,
                downloaded_files=[],
                execution_log=[f"處理結果失敗: {str(e)}"],
                error_details=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                completed_at=datetime.now()
            )
    
    async def _get_execution_logs(self, execution_id: str) -> List[str]:
        """取得機器人執行日誌"""
        try:
            # 這裡應該實作取得執行日誌的邏輯
            # 暫時返回模擬日誌
            return [
                f"開始執行機器人: {execution_id}",
                "正在連接目標網站...",
                "正在執行檢索...",
                "正在下載檔案...",
                "執行完成"
            ]
            
        except Exception as e:
            logger.error(f"取得執行日誌失敗: {str(e)}")
            return [f"無法取得執行日誌: {str(e)}"]
    
    async def _get_downloaded_files(self, execution_id: str) -> List[str]:
        """取得下載的檔案清單"""
        try:
            # 這裡應該實作取得下載檔案的邏輯
            # 暫時返回模擬檔案路徑
            return [
                f"/downloads/{execution_id}/patent_001.pdf",
                f"/downloads/{execution_id}/patent_002.pdf",
                f"/downloads/{execution_id}/search_results.json"
            ]
            
        except Exception as e:
            logger.error(f"取得下載檔案清單失敗: {str(e)}")
            return []
    
    async def _cancel_task(self, task_id: str):
        """取消RPA任務"""
        try:
            if task_id not in self.active_tasks:
                return
            
            # 這裡應該實作取消任務的邏輯
            logger.info(f"正在取消RPA任務: {task_id}")
            
            # 從活躍任務中移除
            del self.active_tasks[task_id]
            
        except Exception as e:
            logger.error(f"取消RPA任務失敗: {task_id}, 錯誤: {str(e)}")
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """取得活躍任務清單"""
        try:
            tasks = []
            
            for task_id, task_info in self.active_tasks.items():
                tasks.append({
                    "task_id": task_id,
                    "status": task_info["status"],
                    "start_time": task_info["start_time"],
                    "duration": (datetime.now() - task_info["start_time"]).total_seconds(),
                    "robot_type": task_info["request"].robot_type,
                    "target_database": task_info["request"].target_database.value
                })
            
            return tasks
            
        except Exception as e:
            logger.error(f"取得活躍任務清單失敗: {str(e)}")
            return []
    
    async def get_robot_status(self) -> Dict[str, Any]:
        """取得機器人狀態"""
        try:
            robot_status = {}
            
            for robot_id, config in self.robot_configs.items():
                # 這裡應該實作檢查機器人狀態的邏輯
                robot_status[robot_id] = {
                    "name": config["name"],
                    "status": "available",  # 實際應該檢查真實狀態
                    "capabilities": config["capabilities"],
                    "target_database": config["target_database"].value if config["target_database"] else "multiple"
                }
            
            return robot_status
            
        except Exception as e:
            logger.error(f"取得機器人狀態失敗: {str(e)}")
            return {}
