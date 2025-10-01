#!/usr/bin/env python3
"""
RPA自動專利比對機器人系統 - 整合測試
"""

import asyncio
import json
import time
import requests
import pytest
from typing import Dict, List, Any
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentRPASystemTests:
    """專利RPA系統整合測試類別"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.rpa_url = f"{base_url}/rpa"
        self.session = requests.Session()
        self.session.timeout = 30
        
    def test_health_checks(self) -> Dict[str, bool]:
        """測試所有服務的健康檢查端點"""
        results = {}
        
        # 測試前端健康檢查
        try:
            response = self.session.get(f"{self.base_url}/")
            results["frontend"] = response.status_code == 200
            logger.info(f"前端健康檢查: {'通過' if results['frontend'] else '失敗'}")
        except Exception as e:
            results["frontend"] = False
            logger.error(f"前端健康檢查失敗: {e}")
        
        # 測試後端API健康檢查
        try:
            response = self.session.get(f"{self.api_url}/health")
            results["backend"] = response.status_code == 200
            logger.info(f"後端API健康檢查: {'通過' if results['backend'] else '失敗'}")
        except Exception as e:
            results["backend"] = False
            logger.error(f"後端API健康檢查失敗: {e}")
        
        # 測試RPA服務健康檢查
        try:
            response = self.session.get(f"{self.rpa_url}/health")
            results["rpa"] = response.status_code == 200
            logger.info(f"RPA服務健康檢查: {'通過' if results['rpa'] else '失敗'}")
        except Exception as e:
            results["rpa"] = False
            logger.error(f"RPA服務健康檢查失敗: {e}")
        
        return results
    
    def test_database_connection(self) -> bool:
        """測試資料庫連接"""
        try:
            response = self.session.get(f"{self.api_url}/database/status")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"資料庫連接測試: 通過 - {data}")
                return True
            else:
                logger.error(f"資料庫連接測試失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"資料庫連接測試失敗: {e}")
            return False
    
    def test_redis_connection(self) -> bool:
        """測試Redis快取連接"""
        try:
            response = self.session.get(f"{self.api_url}/cache/status")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Redis連接測試: 通過 - {data}")
                return True
            else:
                logger.error(f"Redis連接測試失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Redis連接測試失敗: {e}")
            return False
    
    def test_azure_ai_search(self) -> bool:
        """測試Azure AI Search連接"""
        try:
            response = self.session.get(f"{self.api_url}/search/status")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Azure AI Search測試: 通過 - {data}")
                return True
            else:
                logger.error(f"Azure AI Search測試失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Azure AI Search測試失敗: {e}")
            return False
    
    def test_openai_connection(self) -> bool:
        """測試Azure OpenAI連接"""
        try:
            response = self.session.get(f"{self.api_url}/openai/status")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Azure OpenAI測試: 通過 - {data}")
                return True
            else:
                logger.error(f"Azure OpenAI測試失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Azure OpenAI測試失敗: {e}")
            return False
    
    def test_patent_search_api(self) -> bool:
        """測試專利檢索API"""
        try:
            test_query = {
                "query": "人工智慧",
                "databases": ["twpat"],
                "limit": 5
            }
            
            response = self.session.post(
                f"{self.api_url}/patents/search",
                json=test_query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"專利檢索API測試: 通過 - 找到 {len(data.get('results', []))} 筆結果")
                return True
            else:
                logger.error(f"專利檢索API測試失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"專利檢索API測試失敗: {e}")
            return False
    
    def test_rpa_robot_status(self) -> Dict[str, bool]:
        """測試RPA機器人狀態"""
        results = {}
        robots = ["twpat-searcher", "uspto-searcher", "multi-db-searcher"]
        
        for robot in robots:
            try:
                response = self.session.get(f"{self.rpa_url}/robots/{robot}/status")
                results[robot] = response.status_code == 200
                logger.info(f"RPA機器人 {robot} 狀態: {'正常' if results[robot] else '異常'}")
            except Exception as e:
                results[robot] = False
                logger.error(f"RPA機器人 {robot} 狀態檢查失敗: {e}")
        
        return results
    
    def test_file_upload(self) -> bool:
        """測試檔案上傳功能"""
        try:
            # 建立測試檔案
            test_content = "這是一個測試專利文件內容"
            files = {
                'file': ('test_patent.txt', test_content, 'text/plain')
            }
            
            response = self.session.post(
                f"{self.api_url}/documents/upload",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"檔案上傳測試: 通過 - 檔案ID: {data.get('file_id')}")
                return True
            else:
                logger.error(f"檔案上傳測試失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"檔案上傳測試失敗: {e}")
            return False
    
    def test_rag_analysis(self) -> bool:
        """測試RAG智能分析功能"""
        try:
            test_query = {
                "question": "什麼是人工智慧專利的主要技術特徵？",
                "context_limit": 3
            }
            
            response = self.session.post(
                f"{self.api_url}/analysis/rag",
                json=test_query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"RAG分析測試: 通過 - 回應長度: {len(data.get('answer', ''))}")
                return True
            else:
                logger.error(f"RAG分析測試失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"RAG分析測試失敗: {e}")
            return False
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """測試系統效能指標"""
        metrics = {}
        
        # 測試API回應時間
        start_time = time.time()
        try:
            response = self.session.get(f"{self.api_url}/health")
            metrics["api_response_time"] = time.time() - start_time
            metrics["api_status"] = response.status_code == 200
        except Exception as e:
            metrics["api_response_time"] = None
            metrics["api_status"] = False
            logger.error(f"API效能測試失敗: {e}")
        
        # 測試搜尋回應時間
        start_time = time.time()
        try:
            test_query = {"query": "測試", "limit": 1}
            response = self.session.post(
                f"{self.api_url}/patents/search",
                json=test_query,
                headers={"Content-Type": "application/json"}
            )
            metrics["search_response_time"] = time.time() - start_time
            metrics["search_status"] = response.status_code == 200
        except Exception as e:
            metrics["search_response_time"] = None
            metrics["search_status"] = False
            logger.error(f"搜尋效能測試失敗: {e}")
        
        logger.info(f"效能指標: {metrics}")
        return metrics
    
    def run_all_tests(self) -> Dict[str, Any]:
        """執行所有測試"""
        logger.info("開始執行RPA專利比對系統整合測試...")
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "health_checks": self.test_health_checks(),
            "database_connection": self.test_database_connection(),
            "redis_connection": self.test_redis_connection(),
            "azure_ai_search": self.test_azure_ai_search(),
            "openai_connection": self.test_openai_connection(),
            "patent_search_api": self.test_patent_search_api(),
            "rpa_robot_status": self.test_rpa_robot_status(),
            "file_upload": self.test_file_upload(),
            "rag_analysis": self.test_rag_analysis(),
            "performance_metrics": self.test_performance_metrics()
        }
        
        # 計算總體通過率
        total_tests = 0
        passed_tests = 0
        
        for key, value in results.items():
            if key in ["timestamp", "performance_metrics"]:
                continue
            
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    total_tests += 1
                    if sub_value:
                        passed_tests += 1
            elif isinstance(value, bool):
                total_tests += 1
                if value:
                    passed_tests += 1
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
        }
        
        logger.info(f"測試完成 - 通過率: {results['summary']['pass_rate']}% ({passed_tests}/{total_tests})")
        
        return results

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RPA專利比對系統整合測試")
    parser.add_argument("--url", default="http://localhost", help="系統基礎URL")
    parser.add_argument("--output", help="測試結果輸出檔案路徑")
    
    args = parser.parse_args()
    
    # 執行測試
    tester = PatentRPASystemTests(args.url)
    results = tester.run_all_tests()
    
    # 輸出結果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"測試結果已儲存到: {args.output}")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    # 根據測試結果設定退出碼
    if results["summary"]["pass_rate"] < 80:
        logger.error("測試通過率低於80%，系統可能存在問題")
        exit(1)
    else:
        logger.info("所有測試通過，系統運行正常")
        exit(0)

if __name__ == "__main__":
    main()
