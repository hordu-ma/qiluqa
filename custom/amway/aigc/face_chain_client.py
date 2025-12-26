import json
import uuid
import requests
from typing import List
from loguru import logger
from custom.amway.aigc.config.aigc_config import (
    TRAIN_CONN_TIMEOUT,
    TRAIN_READ_TIMEOUT,
    INFER_CONN_TIMEOUT,
    INFER_READ_TIMEOUT,
)
from framework.business_code import ERROR_10911, ERROR_10912
from framework.business_except import BusinessException


class FaceChainClient:

    def __init__(
            self,
            api_url_train: str = "http://10.143.33.239:8008/sdapi/v1/facechain/train",
            api_url_infer: str = "http://10.143.33.239:8008/sdapi/v1/facechain/infer",
            # api_url_train: str = "http://10.140.208.168:80/sdapi/v1/facechain/train",
            # api_url_infer: str = "http://10.140.208.168:80/sdapi/v1/facechain/infer",
            request_id: str = str(uuid.uuid4())
    ):
        # 训练
        self.api_url_train = api_url_train
        # 推理
        self.api_url_infer = api_url_infer
        # 请求唯一标识
        self.request_id = request_id

    def train(
            self,
            img64_list: List[str],
            person_name: str,

    ) -> str:
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            data = {
                # 基模型
                "pretrained_model_name": 'ly261666/cv_portrait_model',
                "revision": "v2.0",
                "sub_path": "film/film",
                "person_name": person_name,
                "train_imgs": img64_list,
            }
            logger.info("###FaceChainClient train request INFO, request_id={}, url={}, person_name={} img64_list.length={}.",
                        self.request_id, self.api_url_train, person_name, len(img64_list))
            response = requests.post(url=self.api_url_train, data=json.dumps(data), headers=headers, timeout=(TRAIN_CONN_TIMEOUT, TRAIN_READ_TIMEOUT))
            logger.info("###FaceChainClient train request INFO, request_id={}, response={}.", self.request_id, response.text)

            if "error" in response.json():
                logger.error("###FaceChainClient train request ERROR, request_id={}, message={}.", self.request_id, response.json()['error'])
                raise BusinessException(ERROR_10911.code, ERROR_10911.message)
            return response.json()
        except BusinessException as e:
            raise e
        except Exception as e:
            logger.error("###FaceChainClient train request ERROR, request_id={}, err={}.", self.request_id, e)

    def infer(
            self,
            style: str,
            person_name: str,
            num_generate: int,
    ) -> str:
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            data = {
                "use_depth_control": False,
                "use_pose_model": False,
                "pose_image": None,
                "multiplier_style": 0.25,
                "multiplier_human": 0.85,
                "base_model": 'ly261666/cv_portrait_model',
                "revision": "v2.0",
                "sub_path": "film/film",
                "style": style,
                "person_name": person_name,
                "num_generate": num_generate,
            }
            logger.info("###FaceChainClient infer request INFO, request_id={}, url={}, body={}.", self.request_id, self.api_url_infer, data)
            response = requests.post(url=self.api_url_infer, data=json.dumps(data), headers=headers, timeout=(INFER_CONN_TIMEOUT, INFER_READ_TIMEOUT))
            if "info" in response.json():
                logger.info("###FaceChainClient infer request INFO, request_id={}, response={}.", self.request_id, response.json()['info'])
                return response.json()['result']

            logger.info("###FaceChainClient infer request INFO, request_id={}, response={}.", self.request_id, response.json())
            if "error" in response.json():
                logger.error("###FaceChainClient infer request ERROR, request_id={}, message={}.", self.request_id, response.json()['error'])
                raise BusinessException(ERROR_10912.code, ERROR_10912.message)
        except BusinessException as e:
            raise e
        except Exception as e:
            logger.error("###FaceChainClient infer request ERROR, request_id={}, err={}.", self.request_id, e)


if __name__ == '__main__':
    client = FaceChainClient()
    client.infer(style="赛博朋克", person_name="ma", num_generate=1)
