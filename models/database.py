"""
資料庫連線與初始化模組
支援PostgreSQL與Azure AI Search
"""

import asyncio
import asyncpg
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
from contextlib import asynccontextmanager

# Azure相關套件
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, SearchableField, VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration
)
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)

class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.search_client: Optional[SearchClient] = None
        self.search_index_client: Optional[SearchIndexClient] = None
        
        # 從環境變數讀取配置
        self.pg_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "patent_rpa"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "password")
        }
        
        self.azure_search_config = {
            "endpoint": os.getenv("AZURE_SEARCH_ENDPOINT"),
            "key": os.getenv("AZURE_SEARCH_KEY"),
            "index_name": os.getenv("AZURE_SEARCH_INDEX", "patents")
        }
    
    async def initialize(self):
        """初始化資料庫連線"""
        try:
            # 初始化PostgreSQL連線池
            await self._init_postgresql()
            
            # 初始化Azure AI Search
            await self._init_azure_search()
            
            # 建立資料表
            await self._create_tables()
            
            logger.info("資料庫初始化完成")
            
        except Exception as e:
            logger.error(f"資料庫初始化失敗: {str(e)}")
            raise
    
    async def _init_postgresql(self):
        """初始化PostgreSQL連線池"""
        try:
            self.pg_pool = await asyncpg.create_pool(
                host=self.pg_config["host"],
                port=self.pg_config["port"],
                database=self.pg_config["database"],
                user=self.pg_config["user"],
                password=self.pg_config["password"],
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("PostgreSQL連線池建立成功")
            
        except Exception as e:
            logger.error(f"PostgreSQL連線失敗: {str(e)}")
            raise
    
    async def _init_azure_search(self):
        """初始化Azure AI Search"""
        try:
            if not self.azure_search_config["endpoint"] or not self.azure_search_config["key"]:
                logger.warning("Azure Search配置不完整，跳過初始化")
                return
            
            credential = AzureKeyCredential(self.azure_search_config["key"])
            
            self.search_index_client = SearchIndexClient(
                endpoint=self.azure_search_config["endpoint"],
                credential=credential
            )
            
            self.search_client = SearchClient(
                endpoint=self.azure_search_config["endpoint"],
                index_name=self.azure_search_config["index_name"],
                credential=credential
            )
            
            # 建立搜尋索引
            await self._create_search_index()
            
            logger.info("Azure AI Search初始化成功")
            
        except Exception as e:
            logger.error(f"Azure AI Search初始化失敗: {str(e)}")
            raise
    
    async def _create_search_index(self):
        """建立Azure AI Search索引"""
        try:
            # 定義索引欄位
            fields = [
                SimpleField(name="patent_id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="patent_number", type=SearchFieldDataType.String),
                SearchableField(name="title", type=SearchFieldDataType.String),
                SearchableField(name="abstract", type=SearchFieldDataType.String),
                SearchableField(name="claims", type=SearchFieldDataType.String),
                SearchableField(name="description", type=SearchFieldDataType.String),
                SearchableField(name="inventors", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SearchableField(name="applicants", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SearchableField(name="ipc_classes", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SimpleField(name="source_database", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="application_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
                SimpleField(name="publication_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,  # OpenAI embedding維度
                    vector_search_profile_name="default-vector-profile"
                )
            ]
            
            # 向量搜尋配置
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="default-vector-profile",
                        algorithm_configuration_name="default-hnsw-config"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="default-hnsw-config"
                    )
                ]
            )
            
            # 建立索引
            index = SearchIndex(
                name=self.azure_search_config["index_name"],
                fields=fields,
                vector_search=vector_search
            )
            
            # 檢查索引是否存在
            try:
                await self.search_index_client.get_index(self.azure_search_config["index_name"])
                logger.info("Azure Search索引已存在")
            except:
                # 索引不存在，建立新索引
                await self.search_index_client.create_index(index)
                logger.info("Azure Search索引建立成功")
                
        except Exception as e:
            logger.error(f"建立Azure Search索引失敗: {str(e)}")
            raise
    
    async def _create_tables(self):
        """建立PostgreSQL資料表"""
        try:
            async with self.pg_pool.acquire() as conn:
                # 建立專利表
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS patents (
                        id SERIAL PRIMARY KEY,
                        patent_id VARCHAR(255) UNIQUE NOT NULL,
                        patent_number VARCHAR(255) NOT NULL,
                        title TEXT NOT NULL,
                        abstract TEXT,
                        inventors JSONB DEFAULT '[]',
                        applicants JSONB DEFAULT '[]',
                        application_date TIMESTAMP,
                        publication_date TIMESTAMP,
                        grant_date TIMESTAMP,
                        ipc_classes JSONB DEFAULT '[]',
                        claims TEXT,
                        description TEXT,
                        images JSONB DEFAULT '[]',
                        source_database VARCHAR(50) NOT NULL,
                        source_url TEXT,
                        vector_embedding TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 建立任務表
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        task_id VARCHAR(255) UNIQUE NOT NULL,
                        user_id VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        request_data JSONB NOT NULL,
                        result_data JSONB,
                        message TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """)
                
                # 建立分析結果表
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id SERIAL PRIMARY KEY,
                        analysis_id VARCHAR(255) UNIQUE NOT NULL,
                        task_id VARCHAR(255) REFERENCES tasks(task_id),
                        patent_id VARCHAR(255) REFERENCES patents(patent_id),
                        analysis_type VARCHAR(100) NOT NULL,
                        result_data JSONB NOT NULL,
                        confidence_score FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 建立索引
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_patents_patent_number ON patents(patent_number)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_patents_source_db ON patents(source_database)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_task_id ON analysis_results(task_id)")
                
                logger.info("PostgreSQL資料表建立成功")
                
        except Exception as e:
            logger.error(f"建立PostgreSQL資料表失敗: {str(e)}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """取得資料庫連線"""
        async with self.pg_pool.acquire() as conn:
            yield conn
    
    async def close(self):
        """關閉資料庫連線"""
        if self.pg_pool:
            await self.pg_pool.close()
        
        if self.search_client:
            await self.search_client.close()
        
        if self.search_index_client:
            await self.search_index_client.close()
        
        logger.info("資料庫連線已關閉")

# 全域資料庫管理器實例
db_manager = DatabaseManager()

async def init_db():
    """初始化資料庫"""
    await db_manager.initialize()

async def get_db_session():
    """取得資料庫會話（依賴注入用）"""
    async with db_manager.get_connection() as conn:
        yield conn

async def close_db():
    """關閉資料庫連線"""
    await db_manager.close()

# 資料庫操作輔助函數

class PatentRepository:
    """專利資料存取層"""
    
    @staticmethod
    async def create_patent(patent_data: Dict[str, Any]) -> str:
        """建立專利記錄"""
        async with db_manager.get_connection() as conn:
            query = """
                INSERT INTO patents (
                    patent_id, patent_number, title, abstract, inventors, 
                    applicants, application_date, publication_date, grant_date,
                    ipc_classes, claims, description, images, source_database, source_url
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                RETURNING patent_id
            """
            
            result = await conn.fetchval(
                query,
                patent_data["patent_id"],
                patent_data["patent_number"],
                patent_data["title"],
                patent_data.get("abstract"),
                json.dumps(patent_data.get("inventors", [])),
                json.dumps(patent_data.get("applicants", [])),
                patent_data.get("application_date"),
                patent_data.get("publication_date"),
                patent_data.get("grant_date"),
                json.dumps(patent_data.get("ipc_classes", [])),
                patent_data.get("claims"),
                patent_data.get("description"),
                json.dumps(patent_data.get("images", [])),
                patent_data["source_database"],
                patent_data.get("source_url")
            )
            
            return result
    
    @staticmethod
    async def get_patent_by_id(patent_id: str) -> Optional[Dict[str, Any]]:
        """根據ID取得專利"""
        async with db_manager.get_connection() as conn:
            query = "SELECT * FROM patents WHERE patent_id = $1"
            row = await conn.fetchrow(query, patent_id)
            
            if row:
                return dict(row)
            return None
    
    @staticmethod
    async def search_patents(
        keywords: Optional[List[str]] = None,
        patent_number: Optional[str] = None,
        source_database: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """搜尋專利"""
        async with db_manager.get_connection() as conn:
            conditions = []
            params = []
            param_count = 0
            
            if keywords:
                keyword_conditions = []
                for keyword in keywords:
                    param_count += 1
                    keyword_conditions.append(f"(title ILIKE ${param_count} OR abstract ILIKE ${param_count})")
                    params.append(f"%{keyword}%")
                conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            if patent_number:
                param_count += 1
                conditions.append(f"patent_number = ${param_count}")
                params.append(patent_number)
            
            if source_database:
                param_count += 1
                conditions.append(f"source_database = ${param_count}")
                params.append(source_database)
            
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            query = f"""
                SELECT * FROM patents 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

class TaskRepository:
    """任務資料存取層"""
    
    @staticmethod
    async def create_task(task_data: Dict[str, Any]) -> str:
        """建立任務記錄"""
        async with db_manager.get_connection() as conn:
            query = """
                INSERT INTO tasks (task_id, user_id, status, request_data, message)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING task_id
            """
            
            result = await conn.fetchval(
                query,
                task_data["task_id"],
                task_data["user_id"],
                task_data["status"],
                json.dumps(task_data["request_data"]),
                task_data.get("message")
            )
            
            return result
    
    @staticmethod
    async def update_task_status(
        task_id: str, 
        status: str, 
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """更新任務狀態"""
        async with db_manager.get_connection() as conn:
            updates = ["status = $2", "updated_at = CURRENT_TIMESTAMP"]
            params = [task_id, status]
            param_count = 2
            
            if progress is not None:
                param_count += 1
                updates.append(f"progress = ${param_count}")
                params.append(progress)
            
            if message is not None:
                param_count += 1
                updates.append(f"message = ${param_count}")
                params.append(message)
            
            if error_message is not None:
                param_count += 1
                updates.append(f"error_message = ${param_count}")
                params.append(error_message)
            
            if status == "completed":
                updates.append("completed_at = CURRENT_TIMESTAMP")
            
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = $1"
            
            await conn.execute(query, *params)
    
    @staticmethod
    async def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
        """根據ID取得任務"""
        async with db_manager.get_connection() as conn:
            query = "SELECT * FROM tasks WHERE task_id = $1"
            row = await conn.fetchrow(query, task_id)
            
            if row:
                return dict(row)
            return None
    
    @staticmethod
    async def get_user_tasks(
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """取得使用者的任務清單"""
        async with db_manager.get_connection() as conn:
            query = """
                SELECT * FROM tasks 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            
            rows = await conn.fetch(query, user_id, limit, offset)
            return [dict(row) for row in rows]
