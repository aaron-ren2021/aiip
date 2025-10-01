#!/usr/bin/env python3
"""
RPA自動專利比對機器人系統 - 負載測試
使用locust進行負載測試
"""

import random
import json
from locust import HttpUser, task, between
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentRPAUser(HttpUser):
    """模擬專利RPA系統使用者"""
    
    wait_time = between(1, 3)  # 使用者操作間隔1-3秒
    
    def on_start(self):
        """使用者開始時的初始化"""
        self.client.verify = False  # 忽略SSL憑證驗證
        logger.info("使用者開始負載測試")
    
    @task(3)
    def health_check(self):
        """健康檢查 - 高頻率任務"""
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"健康檢查失敗: {response.status_code}")
    
    @task(2)
    def search_patents(self):
        """專利檢索 - 中頻率任務"""
        search_queries = [
            "人工智慧",
            "機器學習",
            "深度學習",
            "神經網路",
            "自然語言處理",
            "電腦視覺",
            "語音識別",
            "自動駕駛",
            "物聯網",
            "區塊鏈"
        ]
        
        query = random.choice(search_queries)
        payload = {
            "query": query,
            "databases": ["twpat"],
            "limit": random.randint(5, 20)
        }
        
        with self.client.post(
            "/api/patents/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    result_count = len(data.get("results", []))
                    response.success()
                    logger.info(f"搜尋 '{query}' 找到 {result_count} 筆結果")
                except json.JSONDecodeError:
                    response.failure("回應不是有效的JSON")
            else:
                response.failure(f"專利檢索失敗: {response.status_code}")
    
    @task(1)
    def rag_analysis(self):
        """RAG智能分析 - 低頻率任務"""
        questions = [
            "什麼是人工智慧專利的主要技術特徵？",
            "機器學習專利通常包含哪些技術要素？",
            "深度學習專利的創新點在哪裡？",
            "自然語言處理專利的技術發展趨勢如何？",
            "電腦視覺專利的應用領域有哪些？"
        ]
        
        question = random.choice(questions)
        payload = {
            "question": question,
            "context_limit": random.randint(3, 10)
        }
        
        with self.client.post(
            "/api/analysis/rag",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    answer_length = len(data.get("answer", ""))
                    response.success()
                    logger.info(f"RAG分析問題長度: {len(question)}, 回答長度: {answer_length}")
                except json.JSONDecodeError:
                    response.failure("回應不是有效的JSON")
            else:
                response.failure(f"RAG分析失敗: {response.status_code}")
    
    @task(1)
    def check_rpa_status(self):
        """檢查RPA機器人狀態"""
        robots = ["twpat-searcher", "uspto-searcher", "multi-db-searcher"]
        robot = random.choice(robots)
        
        with self.client.get(f"/rpa/robots/{robot}/status", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                logger.info(f"RPA機器人 {robot} 狀態正常")
            else:
                response.failure(f"RPA機器人 {robot} 狀態檢查失敗: {response.status_code}")
    
    @task(1)
    def upload_document(self):
        """文件上傳測試"""
        # 模擬上傳小型測試文件
        test_content = f"測試專利文件內容 - {random.randint(1000, 9999)}"
        files = {
            'file': (f'test_patent_{random.randint(1, 1000)}.txt', test_content, 'text/plain')
        }
        
        with self.client.post(
            "/api/documents/upload",
            files=files,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    file_id = data.get("file_id")
                    response.success()
                    logger.info(f"文件上傳成功，檔案ID: {file_id}")
                except json.JSONDecodeError:
                    response.failure("回應不是有效的JSON")
            else:
                response.failure(f"文件上傳失敗: {response.status_code}")

class AdminUser(HttpUser):
    """模擬管理員使用者"""
    
    wait_time = between(5, 10)  # 管理員操作間隔較長
    weight = 1  # 管理員使用者權重較低
    
    @task(2)
    def check_system_status(self):
        """檢查系統狀態"""
        endpoints = [
            "/api/database/status",
            "/api/cache/status",
            "/api/search/status",
            "/api/openai/status"
        ]
        
        for endpoint in endpoints:
            with self.client.get(endpoint, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"系統狀態檢查失敗 {endpoint}: {response.status_code}")
    
    @task(1)
    def view_analytics(self):
        """查看分析報告"""
        with self.client.get("/api/analytics/dashboard", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                logger.info("分析報告查看成功")
            else:
                response.failure(f"分析報告查看失敗: {response.status_code}")

class HeavyUser(HttpUser):
    """模擬重度使用者"""
    
    wait_time = between(0.5, 1.5)  # 重度使用者操作頻率更高
    weight = 2  # 重度使用者權重較高
    
    @task(5)
    def intensive_search(self):
        """密集搜尋操作"""
        # 執行多個連續搜尋
        queries = ["AI", "ML", "DL", "NLP", "CV"]
        
        for query in queries:
            payload = {
                "query": query,
                "databases": ["twpat", "uspto"],
                "limit": 50
            }
            
            with self.client.post(
                "/api/patents/search",
                json=payload,
                headers={"Content-Type": "application/json"},
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"密集搜尋失敗: {response.status_code}")
    
    @task(2)
    def batch_analysis(self):
        """批次分析操作"""
        questions = [
            "分析人工智慧專利趨勢",
            "比較不同機器學習演算法專利",
            "評估深度學習專利的技術價值"
        ]
        
        for question in questions:
            payload = {
                "question": question,
                "context_limit": 20
            }
            
            with self.client.post(
                "/api/analysis/rag",
                json=payload,
                headers={"Content-Type": "application/json"},
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"批次分析失敗: {response.status_code}")

# 負載測試配置
if __name__ == "__main__":
    import os
    from locust import run_single_user
    
    # 設定環境變數
    os.environ["LOCUST_HOST"] = "http://localhost"
    
    print("開始單使用者負載測試...")
    print("使用 'locust -f load_tests.py --host=http://your-domain.com' 進行完整負載測試")
    
    # 執行單使用者測試
    run_single_user(PatentRPAUser)
