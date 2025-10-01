"""
TWPAT (中華民國專利檢索系統) 專利檢索機器人
使用Selenium進行自動化檢索
"""

import asyncio
import logging
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from bs4 import BeautifulSoup

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TWPATSearchBot:
    """TWPAT專利檢索機器人"""
    
    def __init__(self, download_dir: str = "/tmp/twpat_downloads"):
        self.base_url = "https://twpat.tipo.gov.tw"
        self.search_url = f"{self.base_url}/tipotwoc/tipotwkm"
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
        # 搜尋結果
        self.search_results: List[Dict[str, Any]] = []
        self.downloaded_files: List[str] = []
        self.execution_log: List[str] = []
    
    def _setup_driver(self):
        """設定Chrome瀏覽器驅動"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # 無頭模式
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
    
    def _navigate_to_search_page(self):
        """導航到檢索頁面"""
        try:
            self.driver.get(self.search_url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            self.execution_log.append(f"已導航到TWPAT檢索頁面: {self.search_url}")
            logger.info("已導航到TWPAT檢索頁面")
            
            # 等待頁面完全載入
            time.sleep(3)
            
        except Exception as e:
            error_msg = f"導航到檢索頁面失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            raise
    
    def _perform_keyword_search(self, keywords: List[str], search_options: Dict[str, Any] = None):
        """執行關鍵字檢索"""
        try:
            # 組合關鍵字
            search_query = " AND ".join(keywords) if len(keywords) > 1 else keywords[0]
            
            self.execution_log.append(f"開始關鍵字檢索: {search_query}")
            logger.info(f"開始關鍵字檢索: {search_query}")
            
            # 尋找檢索輸入框
            search_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "queryString"))
            )
            
            # 清空並輸入檢索詞
            search_input.clear()
            search_input.send_keys(search_query)
            
            # 設定檢索選項
            if search_options:
                self._set_search_options(search_options)
            
            # 點擊檢索按鈕
            search_button = self.driver.find_element(By.NAME, "search")
            search_button.click()
            
            # 等待檢索結果載入
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "result-item")))
            
            self.execution_log.append("關鍵字檢索完成")
            logger.info("關鍵字檢索完成")
            
        except TimeoutException:
            error_msg = "檢索超時或無結果"
            self.execution_log.append(error_msg)
            logger.warning(error_msg)
        except Exception as e:
            error_msg = f"關鍵字檢索失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            raise
    
    def _perform_patent_number_search(self, patent_number: str):
        """執行專利號碼檢索"""
        try:
            self.execution_log.append(f"開始專利號碼檢索: {patent_number}")
            logger.info(f"開始專利號碼檢索: {patent_number}")
            
            # 切換到專利號碼檢索模式
            number_search_tab = self.driver.find_element(By.ID, "numberSearchTab")
            number_search_tab.click()
            
            # 輸入專利號碼
            number_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "patentNumber"))
            )
            number_input.clear()
            number_input.send_keys(patent_number)
            
            # 點擊檢索按鈕
            search_button = self.driver.find_element(By.NAME, "numberSearch")
            search_button.click()
            
            # 等待結果載入
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "patent-detail")))
            
            self.execution_log.append("專利號碼檢索完成")
            logger.info("專利號碼檢索完成")
            
        except Exception as e:
            error_msg = f"專利號碼檢索失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            raise
    
    def _set_search_options(self, options: Dict[str, Any]):
        """設定檢索選項"""
        try:
            # 設定日期範圍
            if options.get("date_range_start"):
                start_date = self.driver.find_element(By.NAME, "startDate")
                start_date.clear()
                start_date.send_keys(options["date_range_start"].strftime("%Y/%m/%d"))
            
            if options.get("date_range_end"):
                end_date = self.driver.find_element(By.NAME, "endDate")
                end_date.clear()
                end_date.send_keys(options["date_range_end"].strftime("%Y/%m/%d"))
            
            # 設定IPC分類
            if options.get("ipc_classes"):
                ipc_input = self.driver.find_element(By.NAME, "ipcClass")
                ipc_input.clear()
                ipc_input.send_keys(", ".join(options["ipc_classes"]))
            
            # 設定結果數量限制
            if options.get("max_results_per_db"):
                results_select = Select(self.driver.find_element(By.NAME, "maxResults"))
                results_select.select_by_value(str(min(options["max_results_per_db"], 500)))
            
            self.execution_log.append("檢索選項設定完成")
            logger.info("檢索選項設定完成")
            
        except Exception as e:
            error_msg = f"設定檢索選項失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.warning(error_msg)
    
    def _extract_search_results(self) -> List[Dict[str, Any]]:
        """提取檢索結果"""
        try:
            results = []
            
            # 尋找結果項目
            result_items = self.driver.find_elements(By.CLASS_NAME, "result-item")
            
            self.execution_log.append(f"找到 {len(result_items)} 筆檢索結果")
            logger.info(f"找到 {len(result_items)} 筆檢索結果")
            
            for i, item in enumerate(result_items):
                try:
                    # 提取基本資訊
                    patent_info = self._extract_patent_info(item)
                    
                    if patent_info:
                        results.append(patent_info)
                        self.execution_log.append(f"已提取第 {i+1} 筆專利資訊")
                    
                except Exception as e:
                    error_msg = f"提取第 {i+1} 筆專利資訊失敗: {str(e)}"
                    self.execution_log.append(error_msg)
                    logger.warning(error_msg)
                    continue
            
            self.search_results = results
            return results
            
        except Exception as e:
            error_msg = f"提取檢索結果失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            return []
    
    def _extract_patent_info(self, result_item) -> Optional[Dict[str, Any]]:
        """從結果項目中提取專利資訊"""
        try:
            patent_info = {}
            
            # 專利號碼
            patent_number_elem = result_item.find_element(By.CLASS_NAME, "patent-number")
            patent_info["patent_number"] = patent_number_elem.text.strip()
            
            # 專利標題
            title_elem = result_item.find_element(By.CLASS_NAME, "patent-title")
            patent_info["title"] = title_elem.text.strip()
            
            # 申請人
            try:
                applicant_elem = result_item.find_element(By.CLASS_NAME, "applicant")
                patent_info["applicants"] = [applicant_elem.text.strip()]
            except NoSuchElementException:
                patent_info["applicants"] = []
            
            # 發明人
            try:
                inventor_elem = result_item.find_element(By.CLASS_NAME, "inventor")
                patent_info["inventors"] = [inventor_elem.text.strip()]
            except NoSuchElementException:
                patent_info["inventors"] = []
            
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
            
            # IPC分類
            try:
                ipc_elem = result_item.find_element(By.CLASS_NAME, "ipc-class")
                patent_info["ipc_classes"] = [ipc_elem.text.strip()]
            except NoSuchElementException:
                patent_info["ipc_classes"] = []
            
            # 詳細頁面連結
            try:
                detail_link = result_item.find_element(By.CLASS_NAME, "detail-link")
                patent_info["detail_url"] = detail_link.get_attribute("href")
            except NoSuchElementException:
                patent_info["detail_url"] = None
            
            # 設定來源資料庫
            patent_info["source_database"] = "twpat"
            patent_info["source_url"] = self.driver.current_url
            
            return patent_info
            
        except Exception as e:
            logger.error(f"提取專利資訊失敗: {str(e)}")
            return None
    
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
            pdf_links = self.driver.find_elements(By.CLASS_NAME, "pdf-download")
            
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
            if patent_info.get("include_images", True):
                image_links = self.driver.find_elements(By.CLASS_NAME, "image-link")
                
                for i, img_link in enumerate(image_links):
                    try:
                        img_url = img_link.get_attribute("src") or img_link.get_attribute("href")
                        
                        if img_url:
                            filename = f"{patent_info['patent_number']}_img_{i+1}.jpg"
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
            # 設定瀏覽器驅動
            self._setup_driver()
            
            # 導航到檢索頁面
            self._navigate_to_search_page()
            
            # 執行檢索
            if patent_number:
                self._perform_patent_number_search(patent_number)
            elif keywords:
                self._perform_keyword_search(keywords, search_options)
            else:
                raise ValueError("必須提供關鍵字或專利號碼")
            
            # 提取檢索結果
            results = self._extract_search_results()
            
            # 下載文件
            all_downloaded_files = []
            
            for patent_info in results:
                if search_options and search_options.get("include_full_text", True):
                    downloaded_files = self._download_patent_documents(patent_info)
                    all_downloaded_files.extend(downloaded_files)
            
            self.downloaded_files = all_downloaded_files
            
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
            
            self.execution_log.append(f"檢索完成，共找到 {len(results)} 筆專利")
            logger.info(f"TWPAT檢索完成，共找到 {len(results)} 筆專利")
            
            return result_summary
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"TWPAT檢索失敗: {str(e)}"
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
    bot = TWPATSearchBot()
    
    # 測試關鍵字檢索
    result = bot.search_patents(
        keywords=["人工智慧", "機器學習"],
        search_options={
            "max_results_per_db": 10,
            "include_full_text": True,
            "include_images": True
        }
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
