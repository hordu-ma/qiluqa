# -*- coding: utf-8 -*-

from config.base_config import *
from langchain_community.embeddings.openai import OpenAIEmbeddings
from loguru import logger

from framework.business_except import BusinessException
from models.embeddings.dashscope.dashscope_embedding_api import DashScopeApiEmbeddings


class EmbeddingsModelAdapter:
    """
    Embeddings稀疏值模型 - 适配器
    """
    openai_api_key: str = OPENAI_API_KEY
    default_model: str = VECTOR_EMBEDDINGS_MODEL
    default_model_type: str = VECTOR_EMBEDDINGS_MODEL_TYPE

    def get_model_instance(
            self,
            model: str = default_model,
            model_type: str = default_model_type
    ):
        """
        获取Embeddings稀疏值模型实例
        :param model: 模型
        :param model_type: 数据集类型
        :return: 模型实例
        """
        try:
            if model == "OpenAI":
                if model_type == "text-embedding-ada-002":
                    return OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            elif model == "DashScope":
                return DashScopeApiEmbeddings()
            else:
                """
                TODO 其他类型的embeddings model
                """
        except Exception as err:
            logger.error("######[10100]EmbeddingsModelAdapter model[{}] invoke error: {}", model, err)
            raise BusinessException(10100, "Embedding对象初始化失败！")
