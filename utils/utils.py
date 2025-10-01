"""
RPA機器人共用工具模組
提供各種實用功能和工具函數
"""

import os
import re
import time
import logging
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import requests
from urllib.parse import urljoin, urlparse
import json

logger = logging.getLogger(__name__)

class PatentNumberNormalizer:
    """專利號碼標準化工具"""
    
    @staticmethod
    def normalize_patent_number(patent_number: str, country: str = "auto") -> str:
        """標準化專利號碼格式"""
        try:
            if not patent_number:
                return ""
            
            # 移除空白和特殊字符
            cleaned = re.sub(r'[^\w\d]', '', patent_number.upper())
            
            # 自動偵測國家
            if country == "auto":
                country = PatentNumberNormalizer._detect_country(cleaned)
            
            # 根據國家格式化
            if country == "US":
                return PatentNumberNormalizer._format_us_patent(cleaned)
            elif country == "TW":
                return PatentNumberNormalizer._format_tw_patent(cleaned)
            elif country == "EP":
                return PatentNumberNormalizer._format_ep_patent(cleaned)
            elif country == "WO":
                return PatentNumberNormalizer._format_wo_patent(cleaned)
            else:
                return cleaned
                
        except Exception as e:
            logger.error(f"標準化專利號碼失敗: {str(e)}")
            return patent_number
    
    @staticmethod
    def _detect_country(patent_number: str) -> str:
        """偵測專利號碼的國家"""
        if patent_number.startswith("US"):
            return "US"
        elif patent_number.startswith("TW"):
            return "TW"
        elif patent_number.startswith("EP"):
            return "EP"
        elif patent_number.startswith("WO"):
            return "WO"
        elif re.match(r'^\d{7,8}$', patent_number):
            return "US"  # 美國專利通常是7-8位數字
        elif re.match(r'^\d{6}$', patent_number):
            return "TW"  # 台灣專利通常是6位數字
        else:
            return "unknown"
    
    @staticmethod
    def _format_us_patent(patent_number: str) -> str:
        """格式化美國專利號碼"""
        # 移除US前綴
        number = patent_number.replace("US", "")
        
        # 確保是數字
        if number.isdigit():
            # 美國專利號碼格式: US1234567
            return f"US{number}"
        
        return patent_number
    
    @staticmethod
    def _format_tw_patent(patent_number: str) -> str:
        """格式化台灣專利號碼"""
        # 移除TW前綴
        number = patent_number.replace("TW", "")
        
        # 確保是數字
        if number.isdigit():
            # 台灣專利號碼格式: TW123456
            return f"TW{number.zfill(6)}"
        
        return patent_number
    
    @staticmethod
    def _format_ep_patent(patent_number: str) -> str:
        """格式化歐洲專利號碼"""
        # 移除EP前綴
        number = patent_number.replace("EP", "")
        
        # 歐洲專利號碼格式: EP1234567
        return f"EP{number}"
    
    @staticmethod
    def _format_wo_patent(patent_number: str) -> str:
        """格式化WIPO專利號碼"""
        # 移除WO前綴
        number = patent_number.replace("WO", "")
        
        # WIPO專利號碼格式: WO2023123456
        return f"WO{number}"

class FileDownloader:
    """檔案下載工具"""
    
    def __init__(self, download_dir: str, timeout: int = 30):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.session = requests.Session()
        
        # 設定User-Agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def download_file(
        self, 
        url: str, 
        filename: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Optional[str]:
        """下載檔案"""
        try:
            # 處理相對URL
            if base_url and not url.startswith("http"):
                url = urljoin(base_url, url)
            
            # 自動生成檔名
            if not filename:
                filename = self._generate_filename(url)
            
            file_path = self.download_dir / filename
            
            # 檢查檔案是否已存在
            if file_path.exists():
                logger.info(f"檔案已存在，跳過下載: {filename}")
                return str(file_path)
            
            # 下載檔案
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # 寫入檔案
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"檔案下載完成: {filename}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"下載檔案失敗 {url}: {str(e)}")
            return None
    
    def _generate_filename(self, url: str) -> str:
        """自動生成檔名"""
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or "." not in filename:
                # 根據Content-Type猜測副檔名
                try:
                    response = self.session.head(url, timeout=10)
                    content_type = response.headers.get('content-type', '')
                    
                    if 'pdf' in content_type:
                        ext = '.pdf'
                    elif 'image' in content_type:
                        ext = '.jpg'
                    elif 'xml' in content_type:
                        ext = '.xml'
                    else:
                        ext = '.bin'
                    
                    filename = f"download_{int(time.time())}{ext}"
                    
                except:
                    filename = f"download_{int(time.time())}.bin"
            
            return filename
            
        except Exception as e:
            logger.error(f"生成檔名失敗: {str(e)}")
            return f"download_{int(time.time())}.bin"
    
    def download_multiple_files(
        self, 
        urls: List[str], 
        base_url: Optional[str] = None
    ) -> List[str]:
        """批量下載檔案"""
        downloaded_files = []
        
        for url in urls:
            try:
                file_path = self.download_file(url, base_url=base_url)
                if file_path:
                    downloaded_files.append(file_path)
            except Exception as e:
                logger.error(f"批量下載失敗 {url}: {str(e)}")
                continue
        
        return downloaded_files

class TextProcessor:
    """文字處理工具"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文字"""
        if not text:
            return ""
        
        # 移除多餘的空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,;:!?()-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """提取關鍵字"""
        try:
            if not text:
                return []
            
            # 簡單的關鍵字提取（基於詞頻）
            words = re.findall(r'\b\w+\b', text.lower())
            
            # 過濾停用詞
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很'
            }
            
            # 計算詞頻
            word_freq = {}
            for word in words:
                if len(word) > 2 and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 排序並返回前N個關鍵字
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            return [word for word, freq in sorted_words[:max_keywords]]
            
        except Exception as e:
            logger.error(f"提取關鍵字失敗: {str(e)}")
            return []
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """計算文字相似度"""
        try:
            if not text1 or not text2:
                return 0.0
            
            # 簡單的Jaccard相似度
            words1 = set(re.findall(r'\b\w+\b', text1.lower()))
            words2 = set(re.findall(r'\b\w+\b', text2.lower()))
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if not union:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"計算文字相似度失敗: {str(e)}")
            return 0.0

class DateProcessor:
    """日期處理工具"""
    
    @staticmethod
    def parse_date(date_string: str) -> Optional[datetime]:
        """解析日期字串"""
        if not date_string:
            return None
        
        # 常見的日期格式
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y年%m月%d日",
            "%Y.%m.%d",
            "%d.%m.%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"無法解析日期: {date_string}")
        return None
    
    @staticmethod
    def format_date(date: datetime, format: str = "%Y-%m-%d") -> str:
        """格式化日期"""
        try:
            return date.strftime(format)
        except Exception as e:
            logger.error(f"格式化日期失敗: {str(e)}")
            return ""
    
    @staticmethod
    def is_date_in_range(
        date: datetime, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> bool:
        """檢查日期是否在範圍內"""
        try:
            if start_date and date < start_date:
                return False
            
            if end_date and date > end_date:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"檢查日期範圍失敗: {str(e)}")
            return True

class ResultValidator:
    """結果驗證工具"""
    
    @staticmethod
    def validate_patent_info(patent_info: Dict[str, Any]) -> bool:
        """驗證專利資訊的完整性"""
        try:
            required_fields = ["patent_number", "title"]
            
            for field in required_fields:
                if not patent_info.get(field):
                    logger.warning(f"專利資訊缺少必要欄位: {field}")
                    return False
            
            # 檢查專利號碼格式
            patent_number = patent_info.get("patent_number", "")
            if not re.match(r'^[A-Z]{2}\d+$|^\d+$', patent_number):
                logger.warning(f"專利號碼格式不正確: {patent_number}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"驗證專利資訊失敗: {str(e)}")
            return False
    
    @staticmethod
    def validate_search_options(search_options: Dict[str, Any]) -> Dict[str, Any]:
        """驗證和標準化檢索選項"""
        try:
            validated_options = {}
            
            # 驗證最大結果數
            max_results = search_options.get("max_results_per_db", 100)
            validated_options["max_results_per_db"] = min(max(max_results, 1), 1000)
            
            # 驗證日期範圍
            if "date_range_start" in search_options:
                start_date = search_options["date_range_start"]
                if isinstance(start_date, str):
                    start_date = DateProcessor.parse_date(start_date)
                validated_options["date_range_start"] = start_date
            
            if "date_range_end" in search_options:
                end_date = search_options["date_range_end"]
                if isinstance(end_date, str):
                    end_date = DateProcessor.parse_date(end_date)
                validated_options["date_range_end"] = end_date
            
            # 驗證布林選項
            bool_options = ["include_full_text", "include_images", "include_claims"]
            for option in bool_options:
                if option in search_options:
                    validated_options[option] = bool(search_options[option])
            
            # 驗證清單選項
            list_options = ["ipc_classes", "search_fields"]
            for option in list_options:
                if option in search_options:
                    value = search_options[option]
                    if isinstance(value, str):
                        validated_options[option] = [value]
                    elif isinstance(value, list):
                        validated_options[option] = value
            
            return validated_options
            
        except Exception as e:
            logger.error(f"驗證檢索選項失敗: {str(e)}")
            return search_options

class PerformanceMonitor:
    """效能監控工具"""
    
    def __init__(self):
        self.start_time = None
        self.checkpoints = {}
    
    def start(self):
        """開始監控"""
        self.start_time = time.time()
        self.checkpoints = {}
    
    def checkpoint(self, name: str):
        """設定檢查點"""
        if self.start_time:
            self.checkpoints[name] = time.time() - self.start_time
    
    def get_elapsed_time(self) -> float:
        """取得總執行時間"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    def get_report(self) -> Dict[str, float]:
        """取得效能報告"""
        report = {
            "total_time": self.get_elapsed_time(),
            "checkpoints": self.checkpoints.copy()
        }
        
        return report

class ConfigManager:
    """配置管理工具"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = {}
        
        if config_file and os.path.exists(config_file):
            self.load_config()
    
    def load_config(self):
        """載入配置檔案"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            logger.info(f"配置檔案載入成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"載入配置檔案失敗: {str(e)}")
    
    def save_config(self):
        """儲存配置檔案"""
        try:
            if self.config_file:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                
                logger.info(f"配置檔案儲存成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"儲存配置檔案失敗: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """取得配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """設定配置值"""
        self.config[key] = value
    
    def update(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
