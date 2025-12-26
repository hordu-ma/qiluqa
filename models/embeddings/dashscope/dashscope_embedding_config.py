from config.base_config import VECTOR_EMBEDDINGS_MODEL_TYPE
from custom.amway.amway_config import DASHSCOPE_API_KEY

DASHSCOPE_EMBEDDINGS_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
DASHSCOPE_EMBEDDINGS_MODEL = None or VECTOR_EMBEDDINGS_MODEL_TYPE
DASHSCOPE_EMBEDDINGS_API_KEY = DASHSCOPE_API_KEY

HTTP_REQUEST_CONN_TIMEOUT = 3
HTTP_REQUEST_READ_TIMEOUT = 5
