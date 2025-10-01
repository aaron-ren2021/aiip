"""
Azure配置管理工具
統一管理Azure服務的配置與連線
"""

import os
import logging
from typing import Dict, Any, Optional
import asyncio
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)

class AzureConfig:
    """Azure配置管理器"""
    
    def __init__(self):
        self.credential: Optional[DefaultAzureCredential] = None
        self.secret_client: Optional[SecretClient] = None
        self.config_cache: Dict[str, str] = {}
        
        # 基本配置
        self.key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        self.location = os.getenv("AZURE_LOCATION", "East Asia")
        
        # 載入環境變數配置
        self._load_env_config()
    
    def _load_env_config(self):
        """從環境變數載入配置"""
        env_configs = {
            # Azure基礎配置
            "AZURE_TENANT_ID": os.getenv("AZURE_TENANT_ID"),
            "AZURE_CLIENT_ID": os.getenv("AZURE_CLIENT_ID"),
            "AZURE_CLIENT_SECRET": os.getenv("AZURE_CLIENT_SECRET"),
            
            # Azure AI Search
            "AZURE_SEARCH_ENDPOINT": os.getenv("AZURE_SEARCH_ENDPOINT"),
            "AZURE_SEARCH_KEY": os.getenv("AZURE_SEARCH_KEY"),
            "AZURE_SEARCH_INDEX": os.getenv("AZURE_SEARCH_INDEX", "patents"),
            
            # Azure OpenAI
            "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "AZURE_OPENAI_KEY": os.getenv("AZURE_OPENAI_KEY"),
            "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            
            # Azure Storage
            "AZURE_STORAGE_ACCOUNT": os.getenv("AZURE_STORAGE_ACCOUNT"),
            "AZURE_STORAGE_KEY": os.getenv("AZURE_STORAGE_KEY"),
            "AZURE_STORAGE_CONTAINER": os.getenv("AZURE_STORAGE_CONTAINER", "patents"),
            
            # Azure Service Bus
            "AZURE_SERVICE_BUS_NAMESPACE": os.getenv("AZURE_SERVICE_BUS_NAMESPACE"),
            "AZURE_SERVICE_BUS_KEY": os.getenv("AZURE_SERVICE_BUS_KEY"),
            "AZURE_SERVICE_BUS_QUEUE": os.getenv("AZURE_SERVICE_BUS_QUEUE", "rpa-tasks"),
            
            # Azure PostgreSQL
            "AZURE_POSTGRES_SERVER": os.getenv("AZURE_POSTGRES_SERVER"),
            "AZURE_POSTGRES_USERNAME": os.getenv("AZURE_POSTGRES_USERNAME"),
            "AZURE_POSTGRES_PASSWORD": os.getenv("AZURE_POSTGRES_PASSWORD"),
            "AZURE_POSTGRES_DATABASE": os.getenv("AZURE_POSTGRES_DATABASE", "patent_rpa"),
            
            # Azure Container Registry
            "AZURE_CONTAINER_REGISTRY": os.getenv("AZURE_CONTAINER_REGISTRY"),
            "AZURE_CONTAINER_REGISTRY_USERNAME": os.getenv("AZURE_CONTAINER_REGISTRY_USERNAME"),
            "AZURE_CONTAINER_REGISTRY_PASSWORD": os.getenv("AZURE_CONTAINER_REGISTRY_PASSWORD"),
            
            # Azure Container Apps
            "AZURE_CONTAINER_APP_ENV": os.getenv("AZURE_CONTAINER_APP_ENV"),
            
            # OpenAI (備用)
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            
            # Automation Anywhere
            "AA_CONTROL_ROOM_URL": os.getenv("AA_CONTROL_ROOM_URL"),
            "AA_USERNAME": os.getenv("AA_USERNAME"),
            "AA_PASSWORD": os.getenv("AA_PASSWORD"),
            "AA_API_KEY": os.getenv("AA_API_KEY"),
            "AA_WORKSPACE_ID": os.getenv("AA_WORKSPACE_ID"),
            "AA_POOL_ID": os.getenv("AA_POOL_ID")
        }
        
        # 過濾掉空值
        self.config_cache = {k: v for k, v in env_configs.items() if v}
    
    async def initialize(self):
        """初始化Azure配置"""
        try:
            logger.info("正在初始化Azure配置...")
            
            # 初始化Azure認證
            await self._init_azure_credential()
            
            # 初始化Key Vault客戶端
            await self._init_key_vault_client()
            
            # 載入Key Vault中的機密
            await self._load_key_vault_secrets()
            
            logger.info("Azure配置初始化完成")
            
        except Exception as e:
            logger.error(f"Azure配置初始化失敗: {str(e)}")
            # 不拋出異常，允許使用環境變數配置
    
    async def _init_azure_credential(self):
        """初始化Azure認證"""
        try:
            self.credential = DefaultAzureCredential()
            
            # 測試認證
            # 這裡可以加入測試認證的邏輯
            
            logger.info("Azure認證初始化成功")
            
        except Exception as e:
            logger.error(f"Azure認證初始化失敗: {str(e)}")
            self.credential = None
    
    async def _init_key_vault_client(self):
        """初始化Key Vault客戶端"""
        try:
            if not self.key_vault_url or not self.credential:
                logger.warning("Key Vault URL或認證不可用，跳過Key Vault初始化")
                return
            
            self.secret_client = SecretClient(
                vault_url=self.key_vault_url,
                credential=self.credential
            )
            
            logger.info("Key Vault客戶端初始化成功")
            
        except Exception as e:
            logger.error(f"Key Vault客戶端初始化失敗: {str(e)}")
            self.secret_client = None
    
    async def _load_key_vault_secrets(self):
        """從Key Vault載入機密"""
        try:
            if not self.secret_client:
                logger.warning("Key Vault客戶端不可用，跳過機密載入")
                return
            
            # 定義需要從Key Vault載入的機密
            secret_mappings = {
                "azure-search-key": "AZURE_SEARCH_KEY",
                "azure-openai-key": "AZURE_OPENAI_KEY",
                "azure-storage-key": "AZURE_STORAGE_KEY",
                "azure-service-bus-key": "AZURE_SERVICE_BUS_KEY",
                "azure-postgres-password": "AZURE_POSTGRES_PASSWORD",
                "openai-api-key": "OPENAI_API_KEY",
                "aa-password": "AA_PASSWORD",
                "aa-api-key": "AA_API_KEY"
            }
            
            for secret_name, config_key in secret_mappings.items():
                try:
                    secret = await self.secret_client.get_secret(secret_name)
                    self.config_cache[config_key] = secret.value
                    logger.debug(f"已載入機密: {secret_name}")
                    
                except Exception as e:
                    logger.debug(f"無法載入機密 {secret_name}: {str(e)}")
                    continue
            
            logger.info(f"已從Key Vault載入 {len(secret_mappings)} 個機密")
            
        except Exception as e:
            logger.error(f"從Key Vault載入機密失敗: {str(e)}")
    
    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """取得配置值"""
        return self.config_cache.get(key, default)
    
    def set_config(self, key: str, value: str):
        """設定配置值"""
        self.config_cache[key] = value
    
    def get_all_config(self) -> Dict[str, str]:
        """取得所有配置"""
        return self.config_cache.copy()
    
    async def check_health(self) -> str:
        """檢查Azure服務健康狀態"""
        try:
            health_status = {}
            
            # 檢查Azure認證
            if self.credential:
                health_status["credential"] = "healthy"
            else:
                health_status["credential"] = "unhealthy"
            
            # 檢查Key Vault
            if self.secret_client:
                try:
                    # 嘗試列出機密（不實際讀取）
                    secret_properties = self.secret_client.list_properties_of_secrets()
                    async for _ in secret_properties:
                        break  # 只檢查是否可以連接
                    health_status["key_vault"] = "healthy"
                except:
                    health_status["key_vault"] = "unhealthy"
            else:
                health_status["key_vault"] = "not_configured"
            
            # 檢查必要配置
            required_configs = [
                "AZURE_SEARCH_ENDPOINT",
                "AZURE_SEARCH_KEY"
            ]
            
            missing_configs = [
                config for config in required_configs 
                if not self.get_config(config)
            ]
            
            if missing_configs:
                health_status["configuration"] = f"missing: {', '.join(missing_configs)}"
            else:
                health_status["configuration"] = "healthy"
            
            # 判斷整體健康狀態
            if all(status == "healthy" for status in health_status.values() if status != "not_configured"):
                return "healthy"
            else:
                return f"unhealthy: {health_status}"
            
        except Exception as e:
            logger.error(f"Azure配置健康檢查失敗: {str(e)}")
            return f"error: {str(e)}"
    
    async def cleanup(self):
        """清理資源"""
        try:
            if self.secret_client:
                await self.secret_client.close()
            
            if self.credential:
                await self.credential.close()
            
            logger.info("Azure配置資源清理完成")
            
        except Exception as e:
            logger.error(f"Azure配置資源清理失敗: {str(e)}")
    
    def get_azure_search_config(self) -> Dict[str, str]:
        """取得Azure AI Search配置"""
        return {
            "endpoint": self.get_config("AZURE_SEARCH_ENDPOINT", ""),
            "key": self.get_config("AZURE_SEARCH_KEY", ""),
            "index": self.get_config("AZURE_SEARCH_INDEX", "patents")
        }
    
    def get_azure_openai_config(self) -> Dict[str, str]:
        """取得Azure OpenAI配置"""
        return {
            "endpoint": self.get_config("AZURE_OPENAI_ENDPOINT", ""),
            "key": self.get_config("AZURE_OPENAI_KEY", ""),
            "api_version": self.get_config("AZURE_OPENAI_API_VERSION", "2024-02-01")
        }
    
    def get_azure_storage_config(self) -> Dict[str, str]:
        """取得Azure Storage配置"""
        return {
            "account": self.get_config("AZURE_STORAGE_ACCOUNT", ""),
            "key": self.get_config("AZURE_STORAGE_KEY", ""),
            "container": self.get_config("AZURE_STORAGE_CONTAINER", "patents")
        }
    
    def get_postgres_config(self) -> Dict[str, str]:
        """取得PostgreSQL配置"""
        return {
            "host": self.get_config("AZURE_POSTGRES_SERVER", "localhost"),
            "username": self.get_config("AZURE_POSTGRES_USERNAME", "postgres"),
            "password": self.get_config("AZURE_POSTGRES_PASSWORD", ""),
            "database": self.get_config("AZURE_POSTGRES_DATABASE", "patent_rpa"),
            "port": "5432"
        }
    
    def get_service_bus_config(self) -> Dict[str, str]:
        """取得Service Bus配置"""
        return {
            "namespace": self.get_config("AZURE_SERVICE_BUS_NAMESPACE", ""),
            "key": self.get_config("AZURE_SERVICE_BUS_KEY", ""),
            "queue": self.get_config("AZURE_SERVICE_BUS_QUEUE", "rpa-tasks")
        }
    
    def get_container_registry_config(self) -> Dict[str, str]:
        """取得Container Registry配置"""
        return {
            "registry": self.get_config("AZURE_CONTAINER_REGISTRY", ""),
            "username": self.get_config("AZURE_CONTAINER_REGISTRY_USERNAME", ""),
            "password": self.get_config("AZURE_CONTAINER_REGISTRY_PASSWORD", "")
        }
    
    def get_automation_anywhere_config(self) -> Dict[str, str]:
        """取得Automation Anywhere配置"""
        return {
            "control_room_url": self.get_config("AA_CONTROL_ROOM_URL", ""),
            "username": self.get_config("AA_USERNAME", ""),
            "password": self.get_config("AA_PASSWORD", ""),
            "api_key": self.get_config("AA_API_KEY", ""),
            "workspace_id": self.get_config("AA_WORKSPACE_ID", ""),
            "pool_id": self.get_config("AA_POOL_ID", "")
        }
    
    def validate_required_config(self) -> List[str]:
        """驗證必要配置"""
        required_configs = [
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SEARCH_KEY"
        ]
        
        missing_configs = []
        
        for config in required_configs:
            if not self.get_config(config):
                missing_configs.append(config)
        
        return missing_configs
    
    def is_production_environment(self) -> bool:
        """判斷是否為生產環境"""
        env = os.getenv("ENVIRONMENT", "development").lower()
        return env in ["production", "prod"]
    
    def get_log_level(self) -> str:
        """取得日誌等級"""
        if self.is_production_environment():
            return os.getenv("LOG_LEVEL", "INFO")
        else:
            return os.getenv("LOG_LEVEL", "DEBUG")
