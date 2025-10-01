"""
USPTO (美國專利商標局) 專利檢索機器人
使用USPTO API和網頁爬蟲進行自動化檢索
"""

import asyncio
import logging
import json
import os
import time
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import xml.etree.ElementTree as ET

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class USPTOSearchBot:
    """USPTO專利檢索機器人"""
    
    def __init__(self, download_dir: str = "/tmp/uspto_downloads"):
        self.base_url = "https://ppubs.uspto.gov"
        self.api_base_url = "https://developer.uspto.gov/api"
        self.search_url = f"{self.base_url}/pubwebapp/static/pages/ppubsbasic.html"
        
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
        # API配置
        self.api_key = os.getenv("USPTO_API_KEY", "")
        
        # 搜尋結果
        self.search_results: List[Dict[str, Any]] = []
        self.downloaded_files: List[str] = []
        self.execution_log: List[str] = []
    
    def _setup_driver(self):
        """設定Chrome瀏覽器驅動"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # 設定下載目錄
            prefs = {
                "download.default_directory": str(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            
            self.execution_log.append("Chrome瀏覽器驅動設定完成")
            logger.info("Chrome瀏覽器驅動設定完成")
            
        except Exception as e:
            error_msg = f"設定瀏覽器驅動失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            raise
    
    def _search_via_api(
        self, 
        keywords: List[str], 
        search_options: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """使用USPTO API進行檢索"""
        try:
            self.execution_log.append("嘗試使用USPTO API進行檢索")
            logger.info("嘗試使用USPTO API進行檢索")
            
            # 構建API查詢
            query = " AND ".join(keywords) if len(keywords) > 1 else keywords[0]
            
            # API端點
            api_url = f"{self.api_base_url}/search/patent"
            
            # 查詢參數
            params = {
                "query": query,
                "format": "json",
                "limit": search_options.get("max_results_per_db", 100) if search_options else 100
            }
            
            # 添加API Key（如果有）
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # 發送API請求
            response = requests.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                api_data = response.json()
                results = self._parse_api_results(api_data)
                
                self.execution_log.append(f"API檢索成功，找到 {len(results)} 筆結果")
                logger.info(f"API檢索成功，找到 {len(results)} 筆結果")
                
                return results
            else:
                self.execution_log.append(f"API檢索失敗: HTTP {response.status_code}")
                logger.warning(f"API檢索失敗: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            error_msg = f"API檢索失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.warning(error_msg)
            return []
    
    def _parse_api_results(self, api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析API檢索結果"""
        results = []
        
        try:
            patents = api_data.get("patents", [])
            
            for patent in patents:
                patent_info = {
                    "patent_number": patent.get("patentNumber", ""),
                    "title": patent.get("title", ""),
                    "abstract": patent.get("abstract", ""),
                    "inventors": patent.get("inventors", []),
                    "applicants": patent.get("applicants", []),
                    "application_date": patent.get("applicationDate"),
                    "publication_date": patent.get("publicationDate"),
                    "grant_date": patent.get("grantDate"),
                    "ipc_classes": patent.get("ipcClasses", []),
                    "claims": patent.get("claims", ""),
                    "description": patent.get("description", ""),
                    "images": patent.get("images", []),
                    "source_database": "uspto",
                    "source_url": patent.get("url", ""),
                    "detail_url": patent.get("detailUrl", "")
                }
                
                results.append(patent_info)
            
        except Exception as e:
            logger.error(f"解析API結果失敗: {str(e)}")
        
        return results
    
    def _search_via_web(
        self, 
        keywords: List[str], 
        patent_number: Optional[str] = None,
        search_options: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """使用網頁介面進行檢索"""
        try:
            self.execution_log.append("使用網頁介面進行檢索")
            logger.info("使用網頁介面進行檢索")
            
            # 導航到檢索頁面
            self.driver.get(self.search_url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            time.sleep(3)  # 等待頁面完全載入
            
            if patent_number:
                return self._perform_patent_number_search_web(patent_number)
            else:
                return self._perform_keyword_search_web(keywords, search_options)
                
        except Exception as e:
            error_msg = f"網頁檢索失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            return []
    
    def _perform_keyword_search_web(
        self, 
        keywords: List[str], 
        search_options: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """執行關鍵字檢索（網頁版）"""
        try:
            # 組合檢索詞
            search_query = " AND ".join(keywords) if len(keywords) > 1 else keywords[0]
            
            self.execution_log.append(f"開始關鍵字檢索: {search_query}")
            logger.info(f"開始關鍵字檢索: {search_query}")
            
            # 尋找檢索輸入框
            search_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "searchText"))
            )
            
            # 輸入檢索詞
            search_input.clear()
            search_input.send_keys(search_query)
            
            # 設定檢索選項
            if search_options:
                self._set_search_options_web(search_options)
            
            # 點擊檢索按鈕
            search_button = self.driver.find_element(By.ID, "searchButton")
            search_button.click()
            
            # 等待結果載入
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-results")))
            
            # 提取結果
            return self._extract_web_results()
            
        except Exception as e:
            error_msg = f"關鍵字檢索失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            return []
    
    def _perform_patent_number_search_web(self, patent_number: str) -> List[Dict[str, Any]]:
        """執行專利號碼檢索（網頁版）"""
        try:
            self.execution_log.append(f"開始專利號碼檢索: {patent_number}")
            logger.info(f"開始專利號碼檢索: {patent_number}")
            
            # 切換到專利號碼檢索
            number_tab = self.driver.find_element(By.ID, "numberSearchTab")
            number_tab.click()
            
            # 輸入專利號碼
            number_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "patentNumber"))
            )
            number_input.clear()
            number_input.send_keys(patent_number)
            
            # 點擊檢索
            search_button = self.driver.find_element(By.ID, "numberSearchButton")
            search_button.click()
            
            # 等待結果
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "patent-detail")))
            
            # 提取結果
            return self._extract_patent_detail()
            
        except Exception as e:
            error_msg = f"專利號碼檢索失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            return []
    
    def _set_search_options_web(self, options: Dict[str, Any]):
        """設定網頁檢索選項"""
        try:
            # 設定日期範圍
            if options.get("date_range_start"):
                start_date = self.driver.find_element(By.ID, "startDate")
                start_date.clear()
                start_date.send_keys(options["date_range_start"].strftime("%m/%d/%Y"))
            
            if options.get("date_range_end"):
                end_date = self.driver.find_element(By.ID, "endDate")
                end_date.clear()
                end_date.send_keys(options["date_range_end"].strftime("%m/%d/%Y"))
            
            # 設定檢索欄位
            if options.get("search_fields"):
                for field in options["search_fields"]:
                    field_checkbox = self.driver.find_element(By.ID, f"field_{field}")
                    if not field_checkbox.is_selected():
                        field_checkbox.click()
            
            self.execution_log.append("網頁檢索選項設定完成")
            logger.info("網頁檢索選項設定完成")
            
        except Exception as e:
            error_msg = f"設定網頁檢索選項失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.warning(error_msg)
    
    def _extract_web_results(self) -> List[Dict[str, Any]]:
        """提取網頁檢索結果"""
        try:
            results = []
            
            # 尋找結果項目
            result_items = self.driver.find_elements(By.CLASS_NAME, "result-item")
            
            self.execution_log.append(f"找到 {len(result_items)} 筆檢索結果")
            logger.info(f"找到 {len(result_items)} 筆檢索結果")
            
            for i, item in enumerate(result_items):
                try:
                    patent_info = self._extract_patent_info_web(item)
                    
                    if patent_info:
                        results.append(patent_info)
                        self.execution_log.append(f"已提取第 {i+1} 筆專利資訊")
                
                except Exception as e:
                    error_msg = f"提取第 {i+1} 筆專利資訊失敗: {str(e)}"
                    self.execution_log.append(error_msg)
                    logger.warning(error_msg)
                    continue
            
            return results
            
        except Exception as e:
            error_msg = f"提取網頁檢索結果失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            return []
    
    def _extract_patent_info_web(self, result_item) -> Optional[Dict[str, Any]]:
        """從網頁結果項目中提取專利資訊"""
        try:
            patent_info = {}
            
            # 專利號碼
            try:
                patent_number_elem = result_item.find_element(By.CLASS_NAME, "patent-number")
                patent_info["patent_number"] = patent_number_elem.text.strip()
            except NoSuchElementException:
                patent_info["patent_number"] = ""
            
            # 專利標題
            try:
                title_elem = result_item.find_element(By.CLASS_NAME, "patent-title")
                patent_info["title"] = title_elem.text.strip()
            except NoSuchElementException:
                patent_info["title"] = ""
            
            # 發明人
            try:
                inventor_elem = result_item.find_element(By.CLASS_NAME, "inventors")
                inventors_text = inventor_elem.text.strip()
                patent_info["inventors"] = [inv.strip() for inv in inventors_text.split(";")]
            except NoSuchElementException:
                patent_info["inventors"] = []
            
            # 申請人
            try:
                applicant_elem = result_item.find_element(By.CLASS_NAME, "assignee")
                patent_info["applicants"] = [applicant_elem.text.strip()]
            except NoSuchElementException:
                patent_info["applicants"] = []
            
            # 申請日期
            try:
                app_date_elem = result_item.find_element(By.CLASS_NAME, "application-date")
                patent_info["application_date"] = app_date_elem.text.strip()
            except NoSuchElementException:
                patent_info["application_date"] = None
            
            # 公開日期
            try:
                pub_date_elem = result_item.find_element(By.CLASS_NAME, "publication-date")
                patent_info["publication_date"] = pub_date_elem.text.strip()
            except NoSuchElementException:
                patent_info["publication_date"] = None
            
            # 摘要
            try:
                abstract_elem = result_item.find_element(By.CLASS_NAME, "abstract")
                patent_info["abstract"] = abstract_elem.text.strip()
            except NoSuchElementException:
                patent_info["abstract"] = ""
            
            # 詳細頁面連結
            try:
                detail_link = result_item.find_element(By.CLASS_NAME, "detail-link")
                patent_info["detail_url"] = detail_link.get_attribute("href")
            except NoSuchElementException:
                patent_info["detail_url"] = None
            
            # 設定來源
            patent_info["source_database"] = "uspto"
            patent_info["source_url"] = self.driver.current_url
            
            return patent_info
            
        except Exception as e:
            logger.error(f"提取專利資訊失敗: {str(e)}")
            return None
    
    def _extract_patent_detail(self) -> List[Dict[str, Any]]:
        """提取專利詳細資訊"""
        try:
            patent_info = {}
            
            # 從詳細頁面提取完整資訊
            # 這裡應該實作詳細的資訊提取邏輯
            
            return [patent_info] if patent_info else []
            
        except Exception as e:
            logger.error(f"提取專利詳細資訊失敗: {str(e)}")
            return []
    
    def _download_patent_documents(self, patent_info: Dict[str, Any]) -> List[str]:
        """下載專利文件"""
        downloaded_files = []
        
        try:
            if not patent_info.get("detail_url"):
                return downloaded_files
            
            # 導航到詳細頁面
            self.driver.get(patent_info["detail_url"])
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "patent-detail")))
            
            # 下載PDF文件
            pdf_links = self.driver.find_elements(By.CLASS_NAME, "pdf-link")
            
            for i, pdf_link in enumerate(pdf_links):
                try:
                    pdf_url = pdf_link.get_attribute("href")
                    
                    if pdf_url:
                        filename = f"{patent_info['patent_number']}_doc_{i+1}.pdf"
                        file_path = self._download_file(pdf_url, filename)
                        
                        if file_path:
                            downloaded_files.append(file_path)
                            self.execution_log.append(f"已下載PDF文件: {filename}")
                
                except Exception as e:
                    error_msg = f"下載PDF文件失敗: {str(e)}"
                    self.execution_log.append(error_msg)
                    logger.warning(error_msg)
                    continue
            
            # 下載圖片
            image_links = self.driver.find_elements(By.CLASS_NAME, "figure-link")
            
            for i, img_link in enumerate(image_links):
                try:
                    img_url = img_link.get_attribute("src") or img_link.get_attribute("href")
                    
                    if img_url:
                        filename = f"{patent_info['patent_number']}_fig_{i+1}.png"
                        file_path = self._download_file(img_url, filename)
                        
                        if file_path:
                            downloaded_files.append(file_path)
                            self.execution_log.append(f"已下載圖片: {filename}")
                
                except Exception as e:
                    error_msg = f"下載圖片失敗: {str(e)}"
                    self.execution_log.append(error_msg)
                    logger.warning(error_msg)
                    continue
            
        except Exception as e:
            error_msg = f"下載專利文件失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
        
        return downloaded_files
    
    def _download_file(self, url: str, filename: str) -> Optional[str]:
        """下載檔案"""
        try:
            # 處理相對URL
            if url.startswith("/"):
                url = self.base_url + url
            elif not url.startswith("http"):
                url = self.base_url + "/" + url
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            file_path = self.download_dir / filename
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"下載檔案失敗 {url}: {str(e)}")
            return None
    
    def search_patents(
        self,
        keywords: Optional[List[str]] = None,
        patent_number: Optional[str] = None,
        search_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """執行專利檢索"""
        start_time = datetime.now()
        
        try:
            results = []
            
            # 優先嘗試API檢索
            if keywords and not patent_number:
                api_results = self._search_via_api(keywords, search_options)
                if api_results:
                    results = api_results
                else:
                    # API失敗，使用網頁檢索
                    self._setup_driver()
                    results = self._search_via_web(keywords, patent_number, search_options)
            else:
                # 專利號碼檢索或API不可用時使用網頁檢索
                self._setup_driver()
                results = self._search_via_web(keywords, patent_number, search_options)
            
            # 下載文件
            all_downloaded_files = []
            
            if self.driver:  # 只有在使用網頁檢索時才下載文件
                for patent_info in results:
                    if search_options and search_options.get("include_full_text", True):
                        downloaded_files = self._download_patent_documents(patent_info)
                        all_downloaded_files.extend(downloaded_files)
            
            self.downloaded_files = all_downloaded_files
            self.search_results = results
            
            # 計算執行時間
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 建立結果摘要
            result_summary = {
                "status": "completed",
                "total_found": len(results),
                "results": results,
                "downloaded_files": all_downloaded_files,
                "execution_time": execution_time,
                "execution_log": self.execution_log
            }
            
            self.execution_log.append(f"USPTO檢索完成，共找到 {len(results)} 筆專利")
            logger.info(f"USPTO檢索完成，共找到 {len(results)} 筆專利")
            
            return result_summary
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"USPTO檢索失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "error": str(e),
                "total_found": 0,
                "results": [],
                "downloaded_files": [],
                "execution_time": execution_time,
                "execution_log": self.execution_log
            }
        
        finally:
            # 清理資源
            if self.driver:
                self.driver.quit()

def main():
    """主函數 - 用於測試"""
    bot = USPTOSearchBot()
    
    # 測試關鍵字檢索
    result = bot.search_patents(
        keywords=["artificial intelligence", "machine learning"],
        search_options={
            "max_results_per_db": 10,
            "include_full_text": True
        }
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
