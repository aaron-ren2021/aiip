"""
RAG智能分析引擎服務模組
整合Azure AI Search與OpenAI，提供專利智能分析功能
參考Dify和RAGFlow的設計模式，並加入AI Agent功能
"""

import asyncio
import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import openai
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

from models.patent_models import (
    RAGAnalysisRequest, RAGAnalysisResult, PatentInfo
)
from models.database import db_manager
from utils.azure_config import AzureConfig

logger = logging.getLogger(__name__)

class RAGService:
    """RAG智能分析服務"""
    
    def __init__(self):
        self.azure_config = AzureConfig()
        self.search_client: Optional[SearchClient] = None
        self.openai_client = None
        self.embedding_model = "text-embedding-ada-002"
        self.chat_model = "gpt-4"
        
        # AI Agent配置
        self.agent_configs = {
            "patent_analyzer": {
                "name": "專利分析專家",
                "role": "專業的專利分析師，擅長技術特徵提取與侵權風險評估",
                "capabilities": ["技術特徵分析", "相似度比對", "侵權風險評估", "迴避設計建議"]
            },
            "prior_art_searcher": {
                "name": "前案檢索專家", 
                "role": "專業的前案檢索專家，擅長找出相關的先前技術",
                "capabilities": ["前案檢索", "技術領域分析", "時間序列分析", "引用關係分析"]
            },
            "legal_advisor": {
                "name": "專利法律顧問",
                "role": "專業的專利法律專家，提供法律觀點與建議",
                "capabilities": ["法律風險評估", "專利有效性分析", "訴訟風險評估", "授權策略建議"]
            }
        }
    
    async def initialize(self):
        """初始化RAG服務"""
        try:
            logger.info("正在初始化RAG智能分析服務...")
            
            # 初始化Azure Search客戶端
            await self._init_search_client()
            
            # 初始化OpenAI客戶端
            await self._init_openai_client()
            
            # 初始化AI Agent
            await self._init_ai_agents()
            
            logger.info("RAG智能分析服務初始化完成")
            
        except Exception as e:
            logger.error(f"RAG服務初始化失敗: {str(e)}")
            raise
    
    async def cleanup(self):
        """清理資源"""
        logger.info("正在清理RAG服務資源...")
        
        if self.search_client:
            await self.search_client.close()
        
        logger.info("RAG服務資源清理完成")
    
    async def check_health(self) -> str:
        """健康檢查"""
        try:
            # 檢查Azure Search連線
            if self.search_client:
                await self.search_client.get_document_count()
            
            # 檢查OpenAI連線
            if self.openai_client:
                await self.openai_client.models.list()
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"RAG服務健康檢查失敗: {str(e)}")
            return "unhealthy"
    
    async def _init_search_client(self):
        """初始化Azure Search客戶端"""
        try:
            search_endpoint = self.azure_config.get_config("AZURE_SEARCH_ENDPOINT")
            search_key = self.azure_config.get_config("AZURE_SEARCH_KEY")
            index_name = self.azure_config.get_config("AZURE_SEARCH_INDEX", "patents")
            
            if not search_endpoint or not search_key:
                logger.warning("Azure Search配置不完整")
                return
            
            credential = AzureKeyCredential(search_key)
            self.search_client = SearchClient(
                endpoint=search_endpoint,
                index_name=index_name,
                credential=credential
            )
            
            logger.info("Azure Search客戶端初始化成功")
            
        except Exception as e:
            logger.error(f"Azure Search客戶端初始化失敗: {str(e)}")
            raise
    
    async def _init_openai_client(self):
        """初始化OpenAI客戶端"""
        try:
            # 優先使用Azure OpenAI
            azure_openai_endpoint = self.azure_config.get_config("AZURE_OPENAI_ENDPOINT")
            azure_openai_key = self.azure_config.get_config("AZURE_OPENAI_KEY")
            
            if azure_openai_endpoint and azure_openai_key:
                self.openai_client = openai.AsyncAzureOpenAI(
                    azure_endpoint=azure_openai_endpoint,
                    api_key=azure_openai_key,
                    api_version="2024-02-01"
                )
                logger.info("Azure OpenAI客戶端初始化成功")
            else:
                # 使用標準OpenAI
                openai_key = self.azure_config.get_config("OPENAI_API_KEY")
                if openai_key:
                    self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
                    logger.info("OpenAI客戶端初始化成功")
                else:
                    logger.warning("OpenAI配置不完整")
            
        except Exception as e:
            logger.error(f"OpenAI客戶端初始化失敗: {str(e)}")
            raise
    
    async def _init_ai_agents(self):
        """初始化AI Agent"""
        try:
            logger.info("正在初始化AI Agent...")
            
            # 為每個Agent建立專門的系統提示
            for agent_id, config in self.agent_configs.items():
                system_prompt = self._create_agent_system_prompt(config)
                config["system_prompt"] = system_prompt
            
            logger.info(f"已初始化 {len(self.agent_configs)} 個AI Agent")
            
        except Exception as e:
            logger.error(f"AI Agent初始化失敗: {str(e)}")
            raise
    
    def _create_agent_system_prompt(self, agent_config: Dict[str, Any]) -> str:
        """建立Agent的系統提示"""
        return f"""
你是一位{agent_config['name']}，{agent_config['role']}。

你的專業能力包括：
{chr(10).join([f"- {capability}" for capability in agent_config['capabilities']])}

請遵循以下原則：
1. 提供專業、準確的分析
2. 基於事實和證據進行判斷
3. 明確指出分析的信心程度
4. 提供具體可行的建議
5. 使用繁體中文回應

當分析專利時，請特別注意：
- 技術特徵的準確提取
- 創新點的識別
- 與現有技術的差異
- 潛在的法律風險
- 商業化的可能性
"""
    
    async def index_patents(self, patents: List[Dict[str, Any]]):
        """將專利資料建立向量索引"""
        try:
            if not self.search_client or not self.openai_client:
                logger.warning("搜尋客戶端或OpenAI客戶端未初始化")
                return
            
            logger.info(f"正在為 {len(patents)} 筆專利建立向量索引...")
            
            documents = []
            
            for patent in patents:
                try:
                    # 建立專利的完整文本
                    full_text = self._create_patent_full_text(patent)
                    
                    # 生成向量嵌入
                    embedding = await self._generate_embedding(full_text)
                    
                    # 準備搜尋文件
                    search_doc = {
                        "patent_id": patent["patent_id"],
                        "patent_number": patent["patent_number"],
                        "title": patent["title"],
                        "abstract": patent.get("abstract", ""),
                        "claims": patent.get("claims", ""),
                        "description": patent.get("description", ""),
                        "inventors": patent.get("inventors", []),
                        "applicants": patent.get("applicants", []),
                        "ipc_classes": patent.get("ipc_classes", []),
                        "source_database": patent["source_database"],
                        "application_date": patent.get("application_date"),
                        "publication_date": patent.get("publication_date"),
                        "content_vector": embedding
                    }
                    
                    documents.append(search_doc)
                    
                except Exception as e:
                    logger.error(f"處理專利向量化失敗: {patent.get('patent_id', 'unknown')}, 錯誤: {str(e)}")
                    continue
            
            # 批次上傳到Azure Search
            if documents:
                await self.search_client.upload_documents(documents)
                logger.info(f"已成功建立 {len(documents)} 筆專利的向量索引")
            
        except Exception as e:
            logger.error(f"建立專利向量索引失敗: {str(e)}")
            raise
    
    def _create_patent_full_text(self, patent: Dict[str, Any]) -> str:
        """建立專利的完整文本用於向量化"""
        parts = []
        
        if patent.get("title"):
            parts.append(f"標題: {patent['title']}")
        
        if patent.get("abstract"):
            parts.append(f"摘要: {patent['abstract']}")
        
        if patent.get("claims"):
            parts.append(f"申請專利範圍: {patent['claims']}")
        
        if patent.get("description"):
            # 限制說明書長度避免超過token限制
            description = patent["description"][:5000]
            parts.append(f"說明書: {description}")
        
        if patent.get("inventors"):
            parts.append(f"發明人: {', '.join(patent['inventors'])}")
        
        if patent.get("ipc_classes"):
            parts.append(f"IPC分類: {', '.join(patent['ipc_classes'])}")
        
        return "\n\n".join(parts)
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本的向量嵌入"""
        try:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"生成向量嵌入失敗: {str(e)}")
            raise
    
    async def analyze_patents(
        self, 
        patent_ids: List[str],
        analysis_type: str = "similarity",
        target_patent: Optional[str] = None
    ) -> List[RAGAnalysisResult]:
        """使用RAG進行專利分析"""
        try:
            logger.info(f"開始分析 {len(patent_ids)} 筆專利，分析類型: {analysis_type}")
            
            results = []
            
            for patent_id in patent_ids:
                try:
                    # 取得專利資料
                    patent_data = await self._get_patent_data(patent_id)
                    
                    if not patent_data:
                        logger.warning(f"找不到專利資料: {patent_id}")
                        continue
                    
                    # 根據分析類型執行不同的分析
                    if analysis_type == "similarity":
                        analysis_result = await self._analyze_similarity(patent_data, target_patent)
                    elif analysis_type == "prior_art":
                        analysis_result = await self._analyze_prior_art(patent_data)
                    elif analysis_type == "infringement":
                        analysis_result = await self._analyze_infringement_risk(patent_data)
                    elif analysis_type == "comprehensive":
                        analysis_result = await self._analyze_comprehensive(patent_data)
                    else:
                        analysis_result = await self._analyze_general(patent_data)
                    
                    results.append(analysis_result)
                    
                except Exception as e:
                    logger.error(f"分析專利失敗: {patent_id}, 錯誤: {str(e)}")
                    continue
            
            logger.info(f"專利分析完成，共產生 {len(results)} 筆結果")
            return results
            
        except Exception as e:
            logger.error(f"專利分析失敗: {str(e)}")
            raise
    
    async def _get_patent_data(self, patent_id: str) -> Optional[Dict[str, Any]]:
        """取得專利資料"""
        try:
            # 從Azure Search取得專利資料
            if self.search_client:
                result = await self.search_client.get_document(key=patent_id)
                return dict(result)
            
            # 備用：從PostgreSQL取得
            async with db_manager.get_connection() as conn:
                query = "SELECT * FROM patents WHERE patent_id = $1"
                row = await conn.fetchrow(query, patent_id)
                
                if row:
                    return dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"取得專利資料失敗: {patent_id}, 錯誤: {str(e)}")
            return None
    
    async def _analyze_similarity(
        self, 
        patent_data: Dict[str, Any], 
        target_patent: Optional[str] = None
    ) -> RAGAnalysisResult:
        """相似度分析"""
        try:
            # 使用專利分析專家Agent
            agent_config = self.agent_configs["patent_analyzer"]
            
            # 建立查詢向量
            query_text = self._create_patent_full_text(patent_data)
            query_vector = await self._generate_embedding(query_text)
            
            # 向量搜尋相似專利
            similar_patents = await self._vector_search(query_vector, top_k=10)
            
            # 使用LLM進行深度分析
            analysis_prompt = f"""
請分析以下專利的技術特徵和創新點：

專利標題：{patent_data.get('title', '')}
專利摘要：{patent_data.get('abstract', '')}
申請專利範圍：{patent_data.get('claims', '')}

相似專利清單：
{self._format_similar_patents(similar_patents)}

請提供：
1. 主要技術特徵分析
2. 創新點識別
3. 與相似專利的差異比較
4. 相似度評分（0-1）
5. 潛在衝突分析
"""
            
            llm_response = await self._call_llm_agent(agent_config, analysis_prompt)
            
            # 解析LLM回應並建立結果
            analysis_result = RAGAnalysisResult(
                patent_id=patent_data["patent_id"],
                analysis_type="similarity",
                summary=llm_response.get("summary", ""),
                detailed_analysis=llm_response.get("detailed_analysis", {}),
                similarity_patents=similar_patents,
                risk_assessment=llm_response.get("risk_assessment", {}),
                recommendations=llm_response.get("recommendations", []),
                confidence_metrics=llm_response.get("confidence_metrics", {}),
                sources=[p["patent_id"] for p in similar_patents]
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"相似度分析失敗: {str(e)}")
            raise
    
    async def _analyze_prior_art(self, patent_data: Dict[str, Any]) -> RAGAnalysisResult:
        """前案分析"""
        try:
            # 使用前案檢索專家Agent
            agent_config = self.agent_configs["prior_art_searcher"]
            
            # 提取關鍵技術詞彙
            tech_keywords = await self._extract_technical_keywords(patent_data)
            
            # 時間序列檢索
            prior_arts = await self._search_prior_art(
                patent_data, 
                tech_keywords,
                before_date=patent_data.get("application_date")
            )
            
            analysis_prompt = f"""
請分析以下專利的前案技術：

專利資訊：
- 標題：{patent_data.get('title', '')}
- 申請日期：{patent_data.get('application_date', '')}
- 技術關鍵字：{', '.join(tech_keywords)}

找到的前案技術：
{self._format_prior_arts(prior_arts)}

請提供：
1. 前案技術分析
2. 技術發展脈絡
3. 創新性評估
4. 可專利性分析
5. 建議的檢索策略
"""
            
            llm_response = await self._call_llm_agent(agent_config, analysis_prompt)
            
            analysis_result = RAGAnalysisResult(
                patent_id=patent_data["patent_id"],
                analysis_type="prior_art",
                summary=llm_response.get("summary", ""),
                detailed_analysis=llm_response.get("detailed_analysis", {}),
                similarity_patents=prior_arts,
                risk_assessment=llm_response.get("risk_assessment", {}),
                recommendations=llm_response.get("recommendations", []),
                confidence_metrics=llm_response.get("confidence_metrics", {}),
                sources=[p["patent_id"] for p in prior_arts]
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"前案分析失敗: {str(e)}")
            raise
    
    async def _analyze_infringement_risk(self, patent_data: Dict[str, Any]) -> RAGAnalysisResult:
        """侵權風險分析"""
        try:
            # 使用專利法律顧問Agent
            agent_config = self.agent_configs["legal_advisor"]
            
            # 檢索相關專利
            related_patents = await self._search_related_patents(patent_data)
            
            analysis_prompt = f"""
請分析以下專利的侵權風險：

專利資訊：
- 標題：{patent_data.get('title', '')}
- 申請專利範圍：{patent_data.get('claims', '')}
- 技術領域：{', '.join(patent_data.get('ipc_classes', []))}

相關專利：
{self._format_related_patents(related_patents)}

請提供：
1. 侵權風險等級評估（高/中/低）
2. 具體風險點分析
3. 法律建議
4. 迴避設計建議
5. 授權策略建議
"""
            
            llm_response = await self._call_llm_agent(agent_config, analysis_prompt)
            
            analysis_result = RAGAnalysisResult(
                patent_id=patent_data["patent_id"],
                analysis_type="infringement",
                summary=llm_response.get("summary", ""),
                detailed_analysis=llm_response.get("detailed_analysis", {}),
                similarity_patents=related_patents,
                risk_assessment=llm_response.get("risk_assessment", {}),
                recommendations=llm_response.get("recommendations", []),
                confidence_metrics=llm_response.get("confidence_metrics", {}),
                sources=[p["patent_id"] for p in related_patents]
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"侵權風險分析失敗: {str(e)}")
            raise
    
    async def _analyze_comprehensive(self, patent_data: Dict[str, Any]) -> RAGAnalysisResult:
        """綜合分析（結合多個Agent）"""
        try:
            # 並行執行多種分析
            similarity_task = self._analyze_similarity(patent_data)
            prior_art_task = self._analyze_prior_art(patent_data)
            infringement_task = self._analyze_infringement_risk(patent_data)
            
            similarity_result, prior_art_result, infringement_result = await asyncio.gather(
                similarity_task, prior_art_task, infringement_task
            )
            
            # 整合分析結果
            comprehensive_analysis = {
                "similarity_analysis": similarity_result.detailed_analysis,
                "prior_art_analysis": prior_art_result.detailed_analysis,
                "infringement_analysis": infringement_result.detailed_analysis
            }
            
            # 綜合風險評估
            risk_assessment = {
                "overall_risk": self._calculate_overall_risk([
                    similarity_result.risk_assessment,
                    prior_art_result.risk_assessment,
                    infringement_result.risk_assessment
                ]),
                "detailed_risks": {
                    "similarity_risk": similarity_result.risk_assessment,
                    "prior_art_risk": prior_art_result.risk_assessment,
                    "infringement_risk": infringement_result.risk_assessment
                }
            }
            
            # 整合建議
            all_recommendations = (
                similarity_result.recommendations +
                prior_art_result.recommendations +
                infringement_result.recommendations
            )
            
            analysis_result = RAGAnalysisResult(
                patent_id=patent_data["patent_id"],
                analysis_type="comprehensive",
                summary="綜合分析報告",
                detailed_analysis=comprehensive_analysis,
                similarity_patents=similarity_result.similarity_patents,
                risk_assessment=risk_assessment,
                recommendations=list(set(all_recommendations)),  # 去重
                confidence_metrics={
                    "similarity_confidence": similarity_result.confidence_metrics,
                    "prior_art_confidence": prior_art_result.confidence_metrics,
                    "infringement_confidence": infringement_result.confidence_metrics
                },
                sources=list(set(
                    similarity_result.sources +
                    prior_art_result.sources +
                    infringement_result.sources
                ))
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"綜合分析失敗: {str(e)}")
            raise
    
    async def _analyze_general(self, patent_data: Dict[str, Any]) -> RAGAnalysisResult:
        """一般分析"""
        try:
            # 使用專利分析專家Agent進行基本分析
            agent_config = self.agent_configs["patent_analyzer"]
            
            analysis_prompt = f"""
請對以下專利進行基本分析：

專利標題：{patent_data.get('title', '')}
專利摘要：{patent_data.get('abstract', '')}
申請專利範圍：{patent_data.get('claims', '')}
技術分類：{', '.join(patent_data.get('ipc_classes', []))}

請提供：
1. 技術特徵摘要
2. 創新點分析
3. 技術價值評估
4. 應用領域分析
5. 商業化潛力評估
"""
            
            llm_response = await self._call_llm_agent(agent_config, analysis_prompt)
            
            analysis_result = RAGAnalysisResult(
                patent_id=patent_data["patent_id"],
                analysis_type="general",
                summary=llm_response.get("summary", ""),
                detailed_analysis=llm_response.get("detailed_analysis", {}),
                similarity_patents=[],
                risk_assessment=llm_response.get("risk_assessment", {}),
                recommendations=llm_response.get("recommendations", []),
                confidence_metrics=llm_response.get("confidence_metrics", {}),
                sources=[]
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"一般分析失敗: {str(e)}")
            raise
    
    async def _call_llm_agent(
        self, 
        agent_config: Dict[str, Any], 
        user_prompt: str
    ) -> Dict[str, Any]:
        """呼叫LLM Agent"""
        try:
            if not self.openai_client:
                raise Exception("OpenAI客戶端未初始化")
            
            messages = [
                {"role": "system", "content": agent_config["system_prompt"]},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.openai_client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )
            
            # 解析回應（這裡簡化處理，實際應該更複雜的解析）
            content = response.choices[0].message.content
            
            return {
                "summary": content[:500],  # 前500字作為摘要
                "detailed_analysis": {"full_response": content},
                "risk_assessment": {"level": "medium"},  # 簡化處理
                "recommendations": ["建議進行更詳細的分析"],
                "confidence_metrics": {"overall_confidence": 0.8}
            }
            
        except Exception as e:
            logger.error(f"呼叫LLM Agent失敗: {str(e)}")
            raise
    
    async def _vector_search(
        self, 
        query_vector: List[float], 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """向量搜尋"""
        try:
            if not self.search_client:
                return []
            
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="content_vector"
            )
            
            results = await self.search_client.search(
                search_text="*",
                vector_queries=[vector_query],
                select=["patent_id", "patent_number", "title", "abstract", "source_database"]
            )
            
            similar_patents = []
            async for result in results:
                similar_patents.append({
                    "patent_id": result["patent_id"],
                    "patent_number": result["patent_number"],
                    "title": result["title"],
                    "abstract": result.get("abstract", ""),
                    "source_database": result["source_database"],
                    "similarity_score": result.get("@search.score", 0)
                })
            
            return similar_patents
            
        except Exception as e:
            logger.error(f"向量搜尋失敗: {str(e)}")
            return []
    
    async def _extract_technical_keywords(self, patent_data: Dict[str, Any]) -> List[str]:
        """提取技術關鍵字"""
        try:
            # 簡化實作，實際應該使用NLP技術
            text = f"{patent_data.get('title', '')} {patent_data.get('abstract', '')}"
            
            # 這裡可以整合更複雜的關鍵字提取邏輯
            keywords = []
            
            # 從IPC分類提取
            if patent_data.get("ipc_classes"):
                keywords.extend(patent_data["ipc_classes"])
            
            # 簡單的關鍵字提取（實際應該更複雜）
            common_tech_terms = ["系統", "方法", "裝置", "電路", "演算法", "處理", "控制", "檢測"]
            for term in common_tech_terms:
                if term in text:
                    keywords.append(term)
            
            return list(set(keywords))
            
        except Exception as e:
            logger.error(f"提取技術關鍵字失敗: {str(e)}")
            return []
    
    async def _search_prior_art(
        self, 
        patent_data: Dict[str, Any], 
        keywords: List[str],
        before_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """搜尋前案技術"""
        try:
            # 實作前案搜尋邏輯
            # 這裡簡化處理，實際應該更複雜
            return []
            
        except Exception as e:
            logger.error(f"搜尋前案技術失敗: {str(e)}")
            return []
    
    async def _search_related_patents(self, patent_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """搜尋相關專利"""
        try:
            # 實作相關專利搜尋邏輯
            # 這裡簡化處理，實際應該更複雜
            return []
            
        except Exception as e:
            logger.error(f"搜尋相關專利失敗: {str(e)}")
            return []
    
    def _format_similar_patents(self, patents: List[Dict[str, Any]]) -> str:
        """格式化相似專利清單"""
        if not patents:
            return "無找到相似專利"
        
        formatted = []
        for i, patent in enumerate(patents[:5], 1):  # 只顯示前5筆
            formatted.append(f"{i}. {patent['title']} (相似度: {patent.get('similarity_score', 0):.2f})")
        
        return "\n".join(formatted)
    
    def _format_prior_arts(self, prior_arts: List[Dict[str, Any]]) -> str:
        """格式化前案技術清單"""
        if not prior_arts:
            return "無找到相關前案技術"
        
        # 實作格式化邏輯
        return "前案技術清單（待實作）"
    
    def _format_related_patents(self, patents: List[Dict[str, Any]]) -> str:
        """格式化相關專利清單"""
        if not patents:
            return "無找到相關專利"
        
        # 實作格式化邏輯
        return "相關專利清單（待實作）"
    
    def _calculate_overall_risk(self, risk_assessments: List[Dict[str, Any]]) -> str:
        """計算整體風險等級"""
        # 簡化的風險計算邏輯
        # 實際應該更複雜的風險評估模型
        return "medium"
