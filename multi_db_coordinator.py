"""
多資料庫檢索協調機器人
協調多個專利資料庫的並行檢索，合併和去重結果
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# 導入專利檢索機器人
from twpat_search_bot import TWPATSearchBot
from uspto_search_bot import USPTOSearchBot

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiDBCoordinator:
    """多資料庫檢索協調器"""
    
    def __init__(self, download_dir: str = "/tmp/multi_db_downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各資料庫檢索機器人
        self.bots = {
            "twpat": TWPATSearchBot(str(self.download_dir / "twpat")),
            "uspto": USPTOSearchBot(str(self.download_dir / "uspto")),
            # 可以添加更多資料庫機器人
        }
        
        # 結果儲存
        self.all_results: List[Dict[str, Any]] = []
        self.merged_results: List[Dict[str, Any]] = []
        self.downloaded_files: List[str] = []
        self.execution_log: List[str] = []
        
        # 去重配置
        self.dedup_fields = ["patent_number", "title"]
        self.similarity_threshold = 0.8
    
    def search_multiple_databases(
        self,
        databases: List[str],
        keywords: Optional[List[str]] = None,
        patent_number: Optional[str] = None,
        search_options: Optional[Dict[str, Any]] = None,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """在多個資料庫中執行檢索"""
        start_time = datetime.now()
        
        try:
            self.execution_log.append(f"開始多資料庫檢索: {', '.join(databases)}")
            logger.info(f"開始多資料庫檢索: {', '.join(databases)}")
            
            if parallel:
                results = self._search_parallel(databases, keywords, patent_number, search_options)
            else:
                results = self._search_sequential(databases, keywords, patent_number, search_options)
            
            # 合併和去重結果
            merged_results = self._merge_and_deduplicate_results(results)
            
            # 收集所有下載的檔案
            all_downloaded_files = []
            for db_result in results.values():
                all_downloaded_files.extend(db_result.get("downloaded_files", []))
            
            self.all_results = list(results.values())
            self.merged_results = merged_results
            self.downloaded_files = all_downloaded_files
            
            # 計算執行時間
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 建立結果摘要
            result_summary = {
                "status": "completed",
                "databases_searched": databases,
                "total_found_by_db": {db: len(result.get("results", [])) for db, result in results.items()},
                "total_found": sum(len(result.get("results", [])) for result in results.values()),
                "merged_count": len(merged_results),
                "deduplication_ratio": self._calculate_dedup_ratio(results, merged_results),
                "results": merged_results,
                "results_by_database": results,
                "downloaded_files": all_downloaded_files,
                "execution_time": execution_time,
                "execution_log": self.execution_log
            }
            
            self.execution_log.append(f"多資料庫檢索完成，共找到 {len(merged_results)} 筆去重後的專利")
            logger.info(f"多資料庫檢索完成，共找到 {len(merged_results)} 筆去重後的專利")
            
            return result_summary
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"多資料庫檢索失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "error": str(e),
                "databases_searched": databases,
                "total_found": 0,
                "merged_count": 0,
                "results": [],
                "downloaded_files": [],
                "execution_time": execution_time,
                "execution_log": self.execution_log
            }
    
    def _search_parallel(
        self,
        databases: List[str],
        keywords: Optional[List[str]],
        patent_number: Optional[str],
        search_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """並行檢索多個資料庫"""
        try:
            self.execution_log.append("使用並行模式檢索")
            logger.info("使用並行模式檢索")
            
            results = {}
            
            # 使用ThreadPoolExecutor進行並行執行
            with ThreadPoolExecutor(max_workers=len(databases)) as executor:
                # 提交所有檢索任務
                future_to_db = {}
                
                for db in databases:
                    if db in self.bots:
                        future = executor.submit(
                            self._search_single_database,
                            db, keywords, patent_number, search_options
                        )
                        future_to_db[future] = db
                    else:
                        self.execution_log.append(f"不支援的資料庫: {db}")
                        logger.warning(f"不支援的資料庫: {db}")
                
                # 收集結果
                for future in as_completed(future_to_db):
                    db = future_to_db[future]
                    try:
                        result = future.result()
                        results[db] = result
                        
                        self.execution_log.append(f"{db} 檢索完成: {result.get('total_found', 0)} 筆結果")
                        logger.info(f"{db} 檢索完成: {result.get('total_found', 0)} 筆結果")
                        
                    except Exception as e:
                        error_msg = f"{db} 檢索失敗: {str(e)}"
                        self.execution_log.append(error_msg)
                        logger.error(error_msg)
                        
                        results[db] = {
                            "status": "failed",
                            "error": str(e),
                            "total_found": 0,
                            "results": [],
                            "downloaded_files": []
                        }
            
            return results
            
        except Exception as e:
            logger.error(f"並行檢索失敗: {str(e)}")
            raise
    
    def _search_sequential(
        self,
        databases: List[str],
        keywords: Optional[List[str]],
        patent_number: Optional[str],
        search_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """順序檢索多個資料庫"""
        try:
            self.execution_log.append("使用順序模式檢索")
            logger.info("使用順序模式檢索")
            
            results = {}
            
            for db in databases:
                try:
                    if db in self.bots:
                        self.execution_log.append(f"開始檢索 {db}")
                        logger.info(f"開始檢索 {db}")
                        
                        result = self._search_single_database(
                            db, keywords, patent_number, search_options
                        )
                        results[db] = result
                        
                        self.execution_log.append(f"{db} 檢索完成: {result.get('total_found', 0)} 筆結果")
                        logger.info(f"{db} 檢索完成: {result.get('total_found', 0)} 筆結果")
                        
                    else:
                        self.execution_log.append(f"不支援的資料庫: {db}")
                        logger.warning(f"不支援的資料庫: {db}")
                        
                        results[db] = {
                            "status": "failed",
                            "error": "不支援的資料庫",
                            "total_found": 0,
                            "results": [],
                            "downloaded_files": []
                        }
                
                except Exception as e:
                    error_msg = f"{db} 檢索失敗: {str(e)}"
                    self.execution_log.append(error_msg)
                    logger.error(error_msg)
                    
                    results[db] = {
                        "status": "failed",
                        "error": str(e),
                        "total_found": 0,
                        "results": [],
                        "downloaded_files": []
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"順序檢索失敗: {str(e)}")
            raise
    
    def _search_single_database(
        self,
        database: str,
        keywords: Optional[List[str]],
        patent_number: Optional[str],
        search_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """檢索單一資料庫"""
        try:
            bot = self.bots[database]
            
            result = bot.search_patents(
                keywords=keywords,
                patent_number=patent_number,
                search_options=search_options
            )
            
            return result
            
        except Exception as e:
            logger.error(f"檢索 {database} 失敗: {str(e)}")
            raise
    
    def _merge_and_deduplicate_results(
        self, 
        results: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合併和去重檢索結果"""
        try:
            self.execution_log.append("開始合併和去重結果")
            logger.info("開始合併和去重結果")
            
            all_patents = []
            
            # 收集所有專利
            for db, result in results.items():
                if result.get("status") == "completed":
                    patents = result.get("results", [])
                    for patent in patents:
                        # 添加來源資料庫資訊
                        patent["source_databases"] = [db]
                        all_patents.append(patent)
            
            # 去重處理
            deduplicated_patents = self._deduplicate_patents(all_patents)
            
            self.execution_log.append(f"去重完成: {len(all_patents)} -> {len(deduplicated_patents)}")
            logger.info(f"去重完成: {len(all_patents)} -> {len(deduplicated_patents)}")
            
            return deduplicated_patents
            
        except Exception as e:
            error_msg = f"合併和去重結果失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)
            return []
    
    def _deduplicate_patents(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重專利清單"""
        try:
            if not patents:
                return []
            
            deduplicated = []
            seen_hashes = set()
            
            for patent in patents:
                # 計算專利的唯一標識
                patent_hash = self._calculate_patent_hash(patent)
                
                if patent_hash not in seen_hashes:
                    seen_hashes.add(patent_hash)
                    deduplicated.append(patent)
                else:
                    # 找到重複的專利，合併來源資料庫資訊
                    for existing_patent in deduplicated:
                        if self._calculate_patent_hash(existing_patent) == patent_hash:
                            # 合併來源資料庫
                            existing_sources = existing_patent.get("source_databases", [])
                            new_sources = patent.get("source_databases", [])
                            
                            combined_sources = list(set(existing_sources + new_sources))
                            existing_patent["source_databases"] = combined_sources
                            
                            # 合併其他可能的資訊
                            self._merge_patent_info(existing_patent, patent)
                            break
            
            return deduplicated
            
        except Exception as e:
            logger.error(f"去重專利清單失敗: {str(e)}")
            return patents
    
    def _calculate_patent_hash(self, patent: Dict[str, Any]) -> str:
        """計算專利的唯一標識雜湊值"""
        try:
            # 使用專利號碼和標題計算雜湊
            patent_number = patent.get("patent_number", "").strip().upper()
            title = patent.get("title", "").strip().lower()
            
            # 移除常見的專利號碼前綴和格式差異
            patent_number = patent_number.replace("US", "").replace("TW", "").replace("-", "").replace(" ", "")
            
            # 組合用於雜湊的字串
            hash_string = f"{patent_number}|{title}"
            
            # 計算MD5雜湊
            return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"計算專利雜湊失敗: {str(e)}")
            return str(hash(str(patent)))
    
    def _merge_patent_info(self, existing_patent: Dict[str, Any], new_patent: Dict[str, Any]):
        """合併專利資訊"""
        try:
            # 合併發明人
            existing_inventors = existing_patent.get("inventors", [])
            new_inventors = new_patent.get("inventors", [])
            combined_inventors = list(set(existing_inventors + new_inventors))
            existing_patent["inventors"] = combined_inventors
            
            # 合併申請人
            existing_applicants = existing_patent.get("applicants", [])
            new_applicants = new_patent.get("applicants", [])
            combined_applicants = list(set(existing_applicants + new_applicants))
            existing_patent["applicants"] = combined_applicants
            
            # 合併IPC分類
            existing_ipc = existing_patent.get("ipc_classes", [])
            new_ipc = new_patent.get("ipc_classes", [])
            combined_ipc = list(set(existing_ipc + new_ipc))
            existing_patent["ipc_classes"] = combined_ipc
            
            # 補充缺失的資訊
            if not existing_patent.get("abstract") and new_patent.get("abstract"):
                existing_patent["abstract"] = new_patent["abstract"]
            
            if not existing_patent.get("claims") and new_patent.get("claims"):
                existing_patent["claims"] = new_patent["claims"]
            
            if not existing_patent.get("description") and new_patent.get("description"):
                existing_patent["description"] = new_patent["description"]
            
            # 合併圖片
            existing_images = existing_patent.get("images", [])
            new_images = new_patent.get("images", [])
            combined_images = list(set(existing_images + new_images))
            existing_patent["images"] = combined_images
            
        except Exception as e:
            logger.error(f"合併專利資訊失敗: {str(e)}")
    
    def _calculate_dedup_ratio(
        self, 
        results: Dict[str, Dict[str, Any]], 
        merged_results: List[Dict[str, Any]]
    ) -> float:
        """計算去重比例"""
        try:
            total_original = sum(len(result.get("results", [])) for result in results.values())
            total_merged = len(merged_results)
            
            if total_original == 0:
                return 0.0
            
            return (total_original - total_merged) / total_original
            
        except Exception as e:
            logger.error(f"計算去重比例失敗: {str(e)}")
            return 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """取得檢索統計資訊"""
        try:
            stats = {
                "total_databases_searched": len(self.bots),
                "total_results_found": len(self.all_results),
                "merged_results_count": len(self.merged_results),
                "total_files_downloaded": len(self.downloaded_files),
                "deduplication_stats": {
                    "original_count": sum(len(result.get("results", [])) for result in self.all_results),
                    "deduplicated_count": len(self.merged_results),
                    "duplicates_removed": sum(len(result.get("results", [])) for result in self.all_results) - len(self.merged_results)
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"取得統計資訊失敗: {str(e)}")
            return {}
    
    def export_results(self, output_file: str, format: str = "json"):
        """匯出檢索結果"""
        try:
            output_path = Path(output_file)
            
            if format.lower() == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "merged_results": self.merged_results,
                        "statistics": self.get_statistics(),
                        "execution_log": self.execution_log
                    }, f, ensure_ascii=False, indent=2)
            
            elif format.lower() == "csv":
                import pandas as pd
                
                # 將結果轉換為DataFrame
                df = pd.DataFrame(self.merged_results)
                df.to_csv(output_path, index=False, encoding="utf-8")
            
            self.execution_log.append(f"結果已匯出到: {output_path}")
            logger.info(f"結果已匯出到: {output_path}")
            
        except Exception as e:
            error_msg = f"匯出結果失敗: {str(e)}"
            self.execution_log.append(error_msg)
            logger.error(error_msg)

def main():
    """主函數 - 用於測試"""
    coordinator = MultiDBCoordinator()
    
    # 測試多資料庫檢索
    result = coordinator.search_multiple_databases(
        databases=["twpat", "uspto"],
        keywords=["人工智慧", "artificial intelligence"],
        search_options={
            "max_results_per_db": 5,
            "include_full_text": False  # 測試時不下載文件
        },
        parallel=True
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 匯出結果
    coordinator.export_results("multi_db_search_results.json")

if __name__ == "__main__":
    main()
