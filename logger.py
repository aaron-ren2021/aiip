"""
日誌配置工具
統一管理系統日誌
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
import json

def setup_logger(
    name: str,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_azure_logging: bool = True
) -> logging.Logger:
    """設定日誌記錄器"""
    
    # 取得日誌等級
    if not log_level:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # 建立記錄器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 避免重複添加處理器
    if logger.handlers:
        return logger
    
    # 建立格式器
    formatter = CustomFormatter()
    
    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 檔案處理器
    if log_file or os.getenv("LOG_FILE"):
        file_path = log_file or os.getenv("LOG_FILE")
        
        # 確保日誌目錄存在
        log_dir = os.path.dirname(file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 使用輪轉檔案處理器
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Azure Application Insights處理器
    if enable_azure_logging and os.getenv("AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING"):
        try:
            from opencensus.ext.azure.log_exporter import AzureLogHandler
            
            azure_handler = AzureLogHandler(
                connection_string=os.getenv("AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING")
            )
            azure_handler.setLevel(logging.WARNING)  # 只記錄警告以上等級到Azure
            azure_handler.setFormatter(formatter)
            logger.addHandler(azure_handler)
            
        except ImportError:
            logger.warning("Azure Application Insights套件未安裝，跳過Azure日誌記錄")
    
    return logger

class CustomFormatter(logging.Formatter):
    """自定義日誌格式器"""
    
    def __init__(self):
        super().__init__()
        
        # 不同等級的顏色
        self.colors = {
            'DEBUG': '\033[36m',    # 青色
            'INFO': '\033[32m',     # 綠色
            'WARNING': '\033[33m',  # 黃色
            'ERROR': '\033[31m',    # 紅色
            'CRITICAL': '\033[35m', # 紫色
            'RESET': '\033[0m'      # 重置
        }
        
        # 基本格式
        self.base_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        
        # 詳細格式（包含檔案和行號）
        self.detailed_format = "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
        
        # JSON格式（用於結構化日誌）
        self.json_format = True if os.getenv("LOG_FORMAT", "").lower() == "json" else False
    
    def format(self, record):
        """格式化日誌記錄"""
        
        if self.json_format:
            return self._format_json(record)
        else:
            return self._format_text(record)
    
    def _format_text(self, record):
        """格式化為文字格式"""
        
        # 選擇格式
        if record.levelno >= logging.ERROR:
            log_format = self.detailed_format
        else:
            log_format = self.base_format
        
        # 添加顏色（僅在控制台輸出時）
        if hasattr(record, 'stream') and record.stream == sys.stdout:
            color = self.colors.get(record.levelname, '')
            reset = self.colors['RESET']
            colored_format = f"{color}{log_format}{reset}"
        else:
            colored_format = log_format
        
        # 建立格式器
        formatter = logging.Formatter(
            colored_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        return formatter.format(record)
    
    def _format_json(self, record):
        """格式化為JSON格式"""
        
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加異常資訊
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加額外欄位
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

class StructuredLogger:
    """結構化日誌記錄器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_api_request(
        self,
        method: str,
        url: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """記錄API請求"""
        extra_fields = {
            "event_type": "api_request",
            "method": method,
            "url": url,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id,
            "request_id": request_id
        }
        
        level = logging.INFO if status_code < 400 else logging.ERROR
        message = f"{method} {url} - {status_code} ({response_time:.3f}s)"
        
        self.logger.log(level, message, extra={'extra_fields': extra_fields})
    
    def log_rpa_task(
        self,
        task_id: str,
        robot_id: str,
        status: str,
        execution_time: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """記錄RPA任務"""
        extra_fields = {
            "event_type": "rpa_task",
            "task_id": task_id,
            "robot_id": robot_id,
            "status": status,
            "execution_time": execution_time,
            "error_message": error_message
        }
        
        level = logging.INFO if status == "completed" else logging.ERROR
        message = f"RPA任務 {task_id} - {status}"
        
        if execution_time:
            message += f" ({execution_time:.3f}s)"
        
        if error_message:
            message += f" - 錯誤: {error_message}"
        
        self.logger.log(level, message, extra={'extra_fields': extra_fields})
    
    def log_rag_analysis(
        self,
        analysis_id: str,
        patent_id: str,
        analysis_type: str,
        execution_time: float,
        confidence_score: Optional[float] = None
    ):
        """記錄RAG分析"""
        extra_fields = {
            "event_type": "rag_analysis",
            "analysis_id": analysis_id,
            "patent_id": patent_id,
            "analysis_type": analysis_type,
            "execution_time": execution_time,
            "confidence_score": confidence_score
        }
        
        message = f"RAG分析 {analysis_id} - {analysis_type} ({execution_time:.3f}s)"
        
        if confidence_score:
            message += f" - 信心度: {confidence_score:.2f}"
        
        self.logger.info(message, extra={'extra_fields': extra_fields})
    
    def log_database_operation(
        self,
        operation: str,
        table: str,
        affected_rows: int,
        execution_time: float,
        error_message: Optional[str] = None
    ):
        """記錄資料庫操作"""
        extra_fields = {
            "event_type": "database_operation",
            "operation": operation,
            "table": table,
            "affected_rows": affected_rows,
            "execution_time": execution_time,
            "error_message": error_message
        }
        
        level = logging.INFO if not error_message else logging.ERROR
        message = f"資料庫操作 {operation} {table} - {affected_rows} 筆 ({execution_time:.3f}s)"
        
        if error_message:
            message += f" - 錯誤: {error_message}"
        
        self.logger.log(level, message, extra={'extra_fields': extra_fields})
    
    def log_azure_service_call(
        self,
        service: str,
        operation: str,
        status: str,
        response_time: float,
        error_message: Optional[str] = None
    ):
        """記錄Azure服務呼叫"""
        extra_fields = {
            "event_type": "azure_service_call",
            "service": service,
            "operation": operation,
            "status": status,
            "response_time": response_time,
            "error_message": error_message
        }
        
        level = logging.INFO if status == "success" else logging.ERROR
        message = f"Azure {service} {operation} - {status} ({response_time:.3f}s)"
        
        if error_message:
            message += f" - 錯誤: {error_message}"
        
        self.logger.log(level, message, extra={'extra_fields': extra_fields})

def get_structured_logger(name: str) -> StructuredLogger:
    """取得結構化日誌記錄器"""
    logger = setup_logger(name)
    return StructuredLogger(logger)

# 預設日誌記錄器
default_logger = setup_logger("patent_rpa_system")

# 匯出常用函數
def log_info(message: str, **kwargs):
    """記錄資訊日誌"""
    default_logger.info(message, extra={'extra_fields': kwargs} if kwargs else None)

def log_warning(message: str, **kwargs):
    """記錄警告日誌"""
    default_logger.warning(message, extra={'extra_fields': kwargs} if kwargs else None)

def log_error(message: str, **kwargs):
    """記錄錯誤日誌"""
    default_logger.error(message, extra={'extra_fields': kwargs} if kwargs else None)

def log_debug(message: str, **kwargs):
    """記錄除錯日誌"""
    default_logger.debug(message, extra={'extra_fields': kwargs} if kwargs else None)
