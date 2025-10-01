"""
專利相關的資料模型定義
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(str, Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PatentDatabase(str, Enum):
    """支援的專利資料庫"""
    TWPAT = "twpat"  # 中華民國專利檢索系統
    USPTO = "uspto"  # 美國專利商標局
    EPO = "epo"      # 歐洲專利局
    WIPO = "wipo"    # 世界智慧財產權組織
    JPO = "jpo"      # 日本特許廳
    CNIPA = "cnipa"  # 中國國家知識產權局
    KIPO = "kipo"    # 韓國特許廳

class SearchOptions(BaseModel):
    """檢索選項"""
    include_images: bool = Field(default=True, description="是否包含圖片")
    include_full_text: bool = Field(default=True, description="是否包含全文")
    date_range_start: Optional[datetime] = Field(default=None, description="檢索起始日期")
    date_range_end: Optional[datetime] = Field(default=None, description="檢索結束日期")
    max_results_per_db: int = Field(default=100, ge=1, le=1000, description="每個資料庫最大結果數")
    language_preference: List[str] = Field(default=["zh-TW", "en"], description="語言偏好")
    ipc_classes: Optional[List[str]] = Field(default=None, description="IPC分類篩選")

class PatentSearchRequest(BaseModel):
    """專利檢索請求"""
    keywords: Optional[List[str]] = Field(default=None, description="檢索關鍵字")
    patent_number: Optional[str] = Field(default=None, description="專利號碼")
    databases: List[PatentDatabase] = Field(default=[PatentDatabase.TWPAT], description="目標資料庫")
    search_options: SearchOptions = Field(default_factory=SearchOptions, description="檢索選項")
    enable_analysis: bool = Field(default=True, description="是否啟用AI分析")
    priority: int = Field(default=5, ge=1, le=10, description="任務優先級")
    
    @validator('keywords', 'patent_number')
    def validate_search_criteria(cls, v, values):
        """驗證檢索條件"""
        if not values.get('keywords') and not v:
            raise ValueError('必須提供關鍵字或專利號碼其中之一')
        return v

class PatentInfo(BaseModel):
    """專利基本資訊"""
    patent_id: str = Field(description="專利唯一識別碼")
    patent_number: str = Field(description="專利號碼")
    title: str = Field(description="專利標題")
    abstract: Optional[str] = Field(default=None, description="專利摘要")
    inventors: List[str] = Field(default=[], description="發明人清單")
    applicants: List[str] = Field(default=[], description="申請人清單")
    application_date: Optional[datetime] = Field(default=None, description="申請日期")
    publication_date: Optional[datetime] = Field(default=None, description="公開日期")
    grant_date: Optional[datetime] = Field(default=None, description="核准日期")
    ipc_classes: List[str] = Field(default=[], description="IPC分類")
    claims: Optional[str] = Field(default=None, description="申請專利範圍")
    description: Optional[str] = Field(default=None, description="說明書內容")
    images: List[str] = Field(default=[], description="圖片URL清單")
    source_database: PatentDatabase = Field(description="來源資料庫")
    source_url: Optional[str] = Field(default=None, description="原始連結")
    
class PatentAnalysis(BaseModel):
    """專利分析結果"""
    patent_id: str = Field(description="專利ID")
    similarity_score: Optional[float] = Field(default=None, ge=0, le=1, description="相似度分數")
    technical_features: List[str] = Field(default=[], description="技術特徵")
    innovation_points: List[str] = Field(default=[], description="創新點")
    potential_conflicts: List[Dict[str, Any]] = Field(default=[], description="潛在衝突")
    infringement_risk: Optional[str] = Field(default=None, description="侵權風險等級")
    recommendations: List[str] = Field(default=[], description="建議")
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1, description="分析可信度")

class PatentSearchResult(BaseModel):
    """專利檢索結果"""
    task_id: str = Field(description="任務ID")
    total_found: int = Field(description="總找到數量")
    patents: List[PatentInfo] = Field(description="專利清單")
    analysis_results: Optional[List[PatentAnalysis]] = Field(default=None, description="分析結果")
    search_summary: Dict[str, Any] = Field(description="檢索摘要")
    execution_time: float = Field(description="執行時間（秒）")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")

class TaskInfo(BaseModel):
    """任務資訊"""
    task_id: str = Field(description="任務ID")
    status: TaskStatus = Field(description="任務狀態")
    progress: int = Field(default=0, ge=0, le=100, description="進度百分比")
    message: Optional[str] = Field(default=None, description="狀態訊息")
    error_message: Optional[str] = Field(default=None, description="錯誤訊息")
    created_at: datetime = Field(description="建立時間")
    updated_at: datetime = Field(description="更新時間")
    estimated_completion: Optional[datetime] = Field(default=None, description="預估完成時間")
    user_id: str = Field(description="使用者ID")

class RPATaskRequest(BaseModel):
    """RPA任務請求"""
    task_id: str = Field(description="任務ID")
    robot_type: str = Field(description="機器人類型")
    target_database: PatentDatabase = Field(description="目標資料庫")
    search_parameters: Dict[str, Any] = Field(description="檢索參數")
    options: Dict[str, Any] = Field(default={}, description="額外選項")

class RPATaskResult(BaseModel):
    """RPA任務結果"""
    task_id: str = Field(description="任務ID")
    robot_id: str = Field(description="機器人ID")
    status: str = Field(description="執行狀態")
    results_count: int = Field(description="結果數量")
    downloaded_files: List[str] = Field(description="下載的檔案清單")
    execution_log: List[str] = Field(description="執行日誌")
    error_details: Optional[str] = Field(default=None, description="錯誤詳情")
    execution_time: float = Field(description="執行時間")
    completed_at: datetime = Field(description="完成時間")

class RAGAnalysisRequest(BaseModel):
    """RAG分析請求"""
    patent_ids: List[str] = Field(description="要分析的專利ID清單")
    analysis_type: str = Field(default="similarity", description="分析類型")
    target_patent: Optional[str] = Field(default=None, description="目標專利（用於比對）")
    custom_prompt: Optional[str] = Field(default=None, description="自定義提示")
    include_citations: bool = Field(default=True, description="是否包含引用")

class RAGAnalysisResult(BaseModel):
    """RAG分析結果"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="分析ID")
    patent_id: str = Field(description="專利ID")
    analysis_type: str = Field(description="分析類型")
    summary: str = Field(description="分析摘要")
    detailed_analysis: Dict[str, Any] = Field(description="詳細分析")
    similarity_patents: List[Dict[str, Any]] = Field(default=[], description="相似專利")
    risk_assessment: Dict[str, Any] = Field(description="風險評估")
    recommendations: List[str] = Field(description="建議")
    confidence_metrics: Dict[str, float] = Field(description="可信度指標")
    sources: List[str] = Field(description="資料來源")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成時間")

class DatabaseStatus(BaseModel):
    """資料庫狀態"""
    database: PatentDatabase = Field(description="資料庫名稱")
    status: str = Field(description="狀態")
    last_updated: Optional[datetime] = Field(default=None, description="最後更新時間")
    total_patents: Optional[int] = Field(default=None, description="總專利數")
    available_features: List[str] = Field(description="可用功能")
    response_time: Optional[float] = Field(default=None, description="回應時間")

class SystemHealth(BaseModel):
    """系統健康狀態"""
    overall_status: str = Field(description="整體狀態")
    services: Dict[str, str] = Field(description="各服務狀態")
    database_connections: Dict[str, bool] = Field(description="資料庫連線狀態")
    active_tasks: int = Field(description="活躍任務數")
    queue_length: int = Field(description="佇列長度")
    system_load: Dict[str, float] = Field(description="系統負載")
    last_check: datetime = Field(default_factory=datetime.now, description="最後檢查時間")

# 資料庫表格模型（用於ORM）

class PatentRecord(BaseModel):
    """專利記錄（資料庫模型）"""
    id: Optional[int] = Field(default=None, description="主鍵")
    patent_id: str = Field(description="專利唯一識別碼")
    patent_number: str = Field(description="專利號碼")
    title: str = Field(description="專利標題")
    abstract: Optional[str] = Field(default=None, description="專利摘要")
    inventors: str = Field(description="發明人（JSON字串）")
    applicants: str = Field(description="申請人（JSON字串）")
    application_date: Optional[datetime] = Field(default=None, description="申請日期")
    publication_date: Optional[datetime] = Field(default=None, description="公開日期")
    grant_date: Optional[datetime] = Field(default=None, description="核准日期")
    ipc_classes: str = Field(description="IPC分類（JSON字串）")
    claims: Optional[str] = Field(default=None, description="申請專利範圍")
    description: Optional[str] = Field(default=None, description="說明書內容")
    images: str = Field(default="[]", description="圖片URL（JSON字串）")
    source_database: str = Field(description="來源資料庫")
    source_url: Optional[str] = Field(default=None, description="原始連結")
    vector_embedding: Optional[str] = Field(default=None, description="向量嵌入")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")

class TaskRecord(BaseModel):
    """任務記錄（資料庫模型）"""
    id: Optional[int] = Field(default=None, description="主鍵")
    task_id: str = Field(description="任務ID")
    user_id: str = Field(description="使用者ID")
    status: str = Field(description="任務狀態")
    progress: int = Field(default=0, description="進度百分比")
    request_data: str = Field(description="請求資料（JSON字串）")
    result_data: Optional[str] = Field(default=None, description="結果資料（JSON字串）")
    message: Optional[str] = Field(default=None, description="狀態訊息")
    error_message: Optional[str] = Field(default=None, description="錯誤訊息")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")
    completed_at: Optional[datetime] = Field(default=None, description="完成時間")
