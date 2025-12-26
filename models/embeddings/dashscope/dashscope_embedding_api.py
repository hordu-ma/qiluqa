from typing import Any, List, Mapping, Optional
import requests
from loguru import logger
from pydantic import BaseModel, Extra
from langchain.embeddings.base import Embeddings
from models.embeddings.dashscope.dashscope_embedding_config import (
    DASHSCOPE_EMBEDDINGS_URL,
    DASHSCOPE_EMBEDDINGS_MODEL,
    HTTP_REQUEST_CONN_TIMEOUT,
    HTTP_REQUEST_READ_TIMEOUT,
    DASHSCOPE_EMBEDDINGS_API_KEY,
)


class DashScopeApiEmbeddings(BaseModel, Embeddings):
    """
    通义千问 - 通用文本向量服务
    """
    api_key: str = DASHSCOPE_EMBEDDINGS_API_KEY
    embeddings_api_url: str = DASHSCOPE_EMBEDDINGS_URL
    emb_model_name: Optional[str] = DASHSCOPE_EMBEDDINGS_MODEL

    class Config:
        extra = Extra.forbid

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {
            "api_key": self.api_key,
            "embeddings_api_url": self.embeddings_api_url,
            "emb_model_name": self.emb_model_name,
        }

    def _embed(
            self,
            input: List[str]
    ) -> List[List[float]]:
        result_list = []
        total = 0
        for i in input:
            try:
                total = total + 1
                embeddings = self._embed_single(content=i, total=total)
            except Exception as err:
                print(err)
                continue
            result_list.append(embeddings)
        return result_list

    def _embed_single(
            self,
            content: str,
            total: int,
    ) -> List[float]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }

        payload = {
            "input": {
                "texts": [content]
            },
            "model": self.emb_model_name,
            "parameters": {
                "text_type": "query",
            },
        }
        try:
            response = requests.post(
                self.embeddings_api_url,
                headers=headers,
                json=payload,
                timeout=(HTTP_REQUEST_CONN_TIMEOUT, HTTP_REQUEST_READ_TIMEOUT)
            )
            logger.info("#############Request DashScope Embeddings INFO, url={}, headers={}, response={}, total={}.",
                        self.embeddings_api_url, headers, response, total)
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error raised by embedding inference endpoint: {e}")

        try:
            parsed_response = response.json()
            if not isinstance(parsed_response, dict):
                raise ValueError(f"Unexpected response type: {parsed_response}")

            output_response = parsed_response["output"]
            if not isinstance(output_response, dict):
                raise ValueError(f"Unexpected response type: {output_response}")

            embeddings_response = output_response["embeddings"]
            if not isinstance(embeddings_response, list):
                raise ValueError(f"Unexpected response type: {embeddings_response}")

            return embeddings_response[0]["embedding"]
        except requests.exceptions.JSONDecodeError as e:
            raise ValueError(
                f"Error raised by inference API: {e}.\nResponse: {response.text}"
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._embed(texts)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        embedding = self._embed([text])[0]
        return embedding


if __name__ == "__main__":
    # print(DashScopeApiEmbeddings().embed_query("你好"))
    print(DashScopeApiEmbeddings().embed_documents(["你好", "我爱中国"]))
