import uuid
from typing import List, Dict
from loguru import logger
import requests
import json
from framework.business_code import ERROR_10901, ERROR_10902
from framework.business_except import BusinessException
from custom.amway.amway_config import (
    BAIDUBCE_ACCESS_TOKEN_URL,
    BAIDUBCE_TEMPERATURE,
    BAIDUBCE_TOP_P,
    BAIDUBCE_PENALTY_SCORE,
    BAIDUBCE_CHAT_URL,
    BAIDUBCE_SECURE_ANSWER,
    BAIDUBCE_INIT_AIGC_URL,
    BAIDUBCE_GET_AIGC_URL,
)
from service.domain.ai_chat_history import ChatHistoryModel


class BaidubceClient:

    def __init__(
            self,
            access_token_url: str = BAIDUBCE_ACCESS_TOKEN_URL,
            temperature: float = BAIDUBCE_TEMPERATURE,
            top_p: float = BAIDUBCE_TOP_P,
            penalty_score: float = BAIDUBCE_PENALTY_SCORE,
            request_id: str = str(uuid.uuid4()),
    ):
        """
        :param access_token_url: token请求地址
        :param temperature: 较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定
        :param top_p: 影响输出文本的多样性，取值越大，生成文本的多样性越强
        :param penalty_score: 通过对已生成的token增加惩罚，减少重复生成的现象
        :param request_id: 请求唯一标识
        """
        self.access_token_url = access_token_url
        self.request_id = request_id
        self.access_token = self.get_access_token()
        self.temperature = temperature
        self.top_p = top_p
        self.penalty_score = penalty_score
        self.chat_url = BAIDUBCE_CHAT_URL.replace("{access_token}", self.access_token)
        self.init_aigc_url = BAIDUBCE_INIT_AIGC_URL.replace("{access_token}", self.access_token)
        self.get_aigc_url = BAIDUBCE_GET_AIGC_URL.replace("{access_token}", self.access_token)

    def get_access_token(self) -> str:
        """
        获取AccessToken信息
        :return: AccessToken
        """
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            payload = ""
            logger.info("###BaidubceClient get_access_token request INFO, request_id={}, url={}, body={}.", self.request_id, self.access_token_url, payload)
            response = requests.post(url=self.access_token_url, data=payload, headers=headers)
            logger.info("###BaidubceClient get_access_token request INFO, request_id={}, response={}.", self.request_id, response.text)
            if "error" in response.text:
                logger.error("###BaidubceClient get_access_token request ERROR, request_id={}, code={}, message={}.", self.request_id, ERROR_10901, response.text)
                raise BusinessException(ERROR_10901.code, ERROR_10901.message)
            data = eval(response.text)
            return str(data["access_token"])
        except Exception as e:
            logger.error("###BaidubceClient get_access_token request ERROR, request_id={}, err={}.", self.request_id, e)

    def chat(
            self,
            ques: str,
            history: List[ChatHistoryModel] = None,
            retry: bool = True,
    ):
        """
        聊天功能
        :param ques: 用户问题
        :param history: 历史聊天
        :param retry: 是否重试
        :return: 回答
        """
        try:
            headers = {
                'Content-Type': 'application/json',
            }

            body = {
                "messages": self._get_messages(ques=ques, retry=retry, history=history),
                "temperature": self.temperature,
                "top_p": self.top_p,
                "penalty_score": self.penalty_score,
            }
            logger.info("###BaidubceClient chat request INFO, request_id={}, url={}, ques={}, body={}.", self.request_id, self.chat_url, ques, body)
            response = requests.post(url=self.chat_url, data=json.dumps(body), headers=headers)
            response_json = response.json()
            logger.info("###BaidubceClient chat request INFO, request_id={}, response={}.", self.request_id, response_json)
            # 千帆业务异常
            if "error_code" in response_json:
                logger.error("###BaidubceClient chat request ERROR, request_id={}, code={}, message={}.", self.request_id, ERROR_10902, response_json)
                raise BusinessException(response_json["error_code"], response_json["error_msg"])
            # 千帆安全风险
            if bool(response_json["need_clear_history"]) and "result" not in response_json:
                if retry:
                    return self.chat(ques=ques, history=history, retry=False)
                return BAIDUBCE_SECURE_ANSWER, False
            return response_json["result"], True
        except BusinessException as be:
            raise be
        except Exception as e:
            logger.error("###BaidubceClient chat request ERROR, request_id={}, err={}.", self.request_id, e)
            raise BusinessException(ERROR_10902.code, ERROR_10902.message)

    def init_aigc(
            self,
            text: str,
            resolution: str,
            style: str,
            num: int = 1
    ):
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            body = {
                "text": text,
                "style": style,
                "resolution": resolution,
                "num": num,
            }
            logger.info("###BaidubceClient init_aigc request INFO, request_id={}, url={}, body={}.", self.request_id, self.init_aigc_url, body)
            response = requests.post(url=self.init_aigc_url, data=json.dumps(body), headers=headers)
            response_json = response.json()
            logger.info("###BaidubceClient init_aigc request INFO, request_id={}, response={}.", self.request_id, response_json)
            # 千帆业务异常
            if "error_code" in response_json:
                logger.error("###BaidubceClient init_aigc request ERROR, request_id={}, code={}, message={}.", self.request_id, ERROR_10902, response_json)
                raise BusinessException(response_json["error_code"], response_json["error_msg"])
            return response_json
        except BusinessException as be:
            raise be
        except Exception as e:
            logger.error("###BaidubceClient chat request ERROR, request_id={}, err={}.", self.request_id, e)
            raise BusinessException(ERROR_10902.code, ERROR_10902.message)

    def get_aigc(
            self,
            taskId: str,
    ):
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            body = {
                "taskId": taskId,
            }
            logger.info("###BaidubceClient get_aigc request INFO, request_id={}, url={}, body={}.", self.request_id, self.get_aigc_url, body)
            response = requests.post(url=self.get_aigc_url, data=json.dumps(body), headers=headers)
            response_json = response.json()
            logger.info("###BaidubceClient get_aigc request INFO, request_id={}, response={}.", self.request_id, response_json)
            # 千帆业务异常
            if "error_code" in response_json:
                logger.error("###BaidubceClient get_aigc request ERROR, request_id={}, code={}, message={}.", self.request_id, ERROR_10902, response_json)
                raise BusinessException(response_json["error_code"], response_json["error_msg"])
            return response_json
        except BusinessException as be:
            raise be
        except Exception as e:
            logger.error("###BaidubceClient chat request ERROR, request_id={}, err={}.", self.request_id, e)
            raise BusinessException(ERROR_10902.code, ERROR_10902.message)

    @staticmethod
    def _get_messages(
            ques: str,
            retry: bool,
            history: List[ChatHistoryModel] = None,
    ) -> List[Dict]:
        messages = []
        if history and len(history) > 0 and retry:
            for h in history[::-1]:
                messages.append({
                    "role": "user",
                    "content": h.question
                })
                messages.append({
                    "role": "assistant",
                    "content": h.answer
                })

        messages.append({
            "role": "user",
            "content": ques
        })
        return messages


if __name__ == '__main__':
    client = BaidubceClient()
    # print(client.chat("习近平的级别"))
    # print(client.init_aigc(text="睡莲", resolution="1024*1024", style="油画"))
    print(client.get_aigc(taskId="8328053"))

