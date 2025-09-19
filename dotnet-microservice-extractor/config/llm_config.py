# from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import Field, SecretStr, PrivateAttr
# from functools import lru_cache
# from openai import AsyncAzureOpenAI
# from pydantic_ai.models.openai import OpenAIModel
# from llama_index.llms.azure_openai import AzureOpenAI
# from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
# from llama_index.core import Settings
# from typing import Optional

# class LLMConfig(BaseSettings):
#     # Azure OpenAI Configuration
#     azure_openai_api_key: SecretStr = Field(..., validation_alias="AZURE_OPENAI_API_KEY")
#     azure_openai_api_version: str = Field(..., validation_alias="AZURE_OPENAI_API_VERSION")
#     azure_openai_endpoint: str = Field(..., validation_alias="AZURE_OPENAI_ENDPOINT")
#     azure_openai_deployment_name: str = Field(..., validation_alias="AZURE_OPENAI_DEPLOYMENT_NAME")

#     # Azure OpenAI Embedding Configuration
#     azure_openai_embed_api_endpoint: str = Field(..., validation_alias="AZURE_OPENAI_EMBED_API_ENDPOINT")
#     azure_openai_embed_api_key: SecretStr = Field(..., validation_alias="AZURE_OPENAI_EMBED_API_KEY")
#     azure_openai_embed_model: str = Field(..., validation_alias="AZURE_OPENAI_EMBED_MODEL")
#     azure_openai_embed_version: str = Field(..., validation_alias="AZURE_OPENAI_EMBED_VERSION")

#     # LlamaIndex components
#     _llm: Optional[AzureOpenAI] = PrivateAttr(default=None)
#     _embed_model: Optional[AzureOpenAIEmbedding] = PrivateAttr(default=None)

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore"
#     )

#     @classmethod
#     @lru_cache(maxsize=1)
#     def get_pydantic_model(cls, api_key: str, api_version: str, endpoint: str, deployment_name: str) -> OpenAIModel:
#         return OpenAIModel(
#             deployment_name, 
#             openai_client=AsyncAzureOpenAI(
#                 api_key=api_key,
#                 api_version=api_version,
#                 azure_endpoint=endpoint,
#                 azure_deployment=deployment_name
#             )
#         )

#     def init_llamaindex(self) -> None:
#         """Initialize LlamaIndex settings with Azure OpenAI components"""
#         self._llm = AzureOpenAI(
#             model="gpt-4o",
#             deployment_name=self.azure_openai_deployment_name,
#             api_key=self.azure_openai_api_key.get_secret_value(),
#             azure_endpoint=self.azure_openai_endpoint,
#             api_version=self.azure_openai_api_version,
#         )

#         self._embed_model = AzureOpenAIEmbedding(
#             model="text-embedding-3-large",
#             deployment_name=self.azure_openai_embed_model,
#             api_key=self.azure_openai_embed_api_key.get_secret_value(),
#             azure_endpoint=self.azure_openai_embed_api_endpoint,
#             api_version=self.azure_openai_embed_version,
#         )

#         # Configure global LlamaIndex settings
#         Settings.llm = self._llm
#         Settings.embed_model = self._embed_model

# # Create singleton instances
# llm_config = LLMConfig()
# llm_config.init_llamaindex()

# pydantic_ai_model = llm_config.get_pydantic_model(
#     api_key=llm_config.azure_openai_api_key.get_secret_value(),
#     api_version=llm_config.azure_openai_api_version,
#     endpoint=llm_config.azure_openai_endpoint,
#     deployment_name=llm_config.azure_openai_deployment_name
# )


import os
import certifi
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, PrivateAttr
from functools import lru_cache
from openai import AsyncAzureOpenAI
from pydantic_ai.models.openai import OpenAIModel
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from typing import Optional
 

class LLMConfig(BaseSettings):
    # Azure OpenAI Configuration
    azure_openai_api_key: SecretStr = Field(..., validation_alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(..., validation_alias="AZURE_OPENAI_API_VERSION")
    azure_openai_endpoint: str = Field(..., validation_alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: str = Field(..., validation_alias="AZURE_OPENAI_DEPLOYMENT_NAME")
 
    # Azure OpenAI Embedding Configuration
    azure_openai_embed_api_endpoint: str = Field(..., validation_alias="AZURE_OPENAI_EMBED_API_ENDPOINT")
    azure_openai_embed_api_key: SecretStr = Field(..., validation_alias="AZURE_OPENAI_EMBED_API_KEY")
    azure_openai_embed_model: str = Field(..., validation_alias="AZURE_OPENAI_EMBED_MODEL")
    azure_openai_embed_version: str = Field(..., validation_alias="AZURE_OPENAI_EMBED_VERSION")
 
    # LlamaIndex components
    _llm: Optional[AzureOpenAI] = PrivateAttr(default=None)
    _embed_model: Optional[AzureOpenAIEmbedding] = PrivateAttr(default=None)
 
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
 
    @classmethod
    @lru_cache(maxsize=1)
    def get_pydantic_model(cls, api_key: str, api_version: str, endpoint: str, deployment_name: str) -> OpenAIModel:
        return OpenAIModel(
            deployment_name,
            openai_client=AsyncAzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                timeout=120.0, 
                max_retries=3
            )
        )
 
    def init_llamaindex(self) -> None:
        """Initialize LlamaIndex settings with Azure OpenAI components"""
        self._llm = AzureOpenAI(
            model="gpt-4o",
            deployment_name=self.azure_openai_deployment_name,
            api_key=self.azure_openai_api_key.get_secret_value(),
            azure_endpoint=self.azure_openai_endpoint,
            api_version=self.azure_openai_api_version,
            timeout=120.0,  # Set timeout to 120 seconds
            max_retries=3
            
        )
 
        # self._embed_model = AzureOpenAIEmbedding(
        #     model="text-embedding-3-large",
        #     deployment_name=self.azure_openai_embed_model,
        #     api_key=self.azure_openai_embed_api_key.get_secret_value(),
        #     azure_endpoint=self.azure_openai_embed_api_endpoint,
        #     api_version=self.azure_openai_embed_version,
        # )
        
        self._embed_model = AzureOpenAIEmbedding(
            model="text-embedding-3-large",
            api_key=self.azure_openai_embed_api_key.get_secret_value(),
            azure_endpoint=self.azure_openai_embed_api_endpoint,
            api_version=self.azure_openai_embed_version,
            timeout=120.0,  # Set timeout to 120 seconds
            max_retries=3
        )
 
        # self._embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
 
        # Configure global LlamaIndex settings
        Settings.llm = self._llm
        Settings.embed_model = self._embed_model
 
# Create singleton instances
llm_config = LLMConfig()
llm_config.init_llamaindex()
 
pydantic_ai_model = llm_config.get_pydantic_model(
    api_key=llm_config.azure_openai_api_key.get_secret_value(),
    api_version=llm_config.azure_openai_api_version,
    endpoint=llm_config.azure_openai_endpoint,
    deployment_name=llm_config.azure_openai_deployment_name
)
 