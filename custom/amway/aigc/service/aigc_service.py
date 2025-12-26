import base64
import json
import os
import uuid
import numpy as np
import cv2
from loguru import logger
from custom.amway.aigc.face_chain_client import FaceChainClient
from custom.amway.aigc.infer_param import InferParam
from custom.amway.aigc.train_param import TrainParam
from framework.business_code import ERROR_10910
from framework.business_except import BusinessException
from framework.util.id_worker import IdWorker
from service.domain.ai_chat_images import AiChatImagesDomain


def encode_image_to_base64(image_path):
    """
    读取本地图片文件，保存为base64编码数据
    :param image_path: 图片全地址
    :return: 图片序列代码
    """
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_data = base64.b64encode(image_data).decode("utf-8")
    return base64_data


class AmwayAIGC:

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        self.request_id = request_id

    def train(self, param: TrainParam):
        chatImagesDomain = AiChatImagesDomain(request_id=self.request_id)
        chatImagesModel = chatImagesDomain.find_by_id(images_id=param.chat_images_id)
        if not chatImagesModel:
            logger.error("AmwayAIGC train error, chatImagesModel is not empty, request_id={}, chat_images_id={}.", self.request_id, param.chat_images_id)
            raise BusinessException(ERROR_10910.code, ERROR_10910.message)

        # 生成人物名称标识信息
        person_name = chatImagesModel.user_id+"_"+str(IdWorker().get_id())
        # 转换图片序列列表信息
        img64_list = [encode_image_to_base64(img["path"]) for img in json.loads(chatImagesModel.source)]
        client = FaceChainClient(request_id=self.request_id)
        try:
            client.train(img64_list=img64_list, person_name=person_name)
        except BusinessException as e:
            chatImagesDomain.update(
                images_id=param.chat_images_id,
                images_status="fail_to_train",
                images_uuid=person_name,
            )
            raise e
        # 更新图片生成状态
        chatImagesDomain.update(
            images_id=param.chat_images_id,
            images_status="train",
            images_uuid=person_name,
        )

    def infer(self, param: InferParam):
        chatImagesDomain = AiChatImagesDomain(request_id=self.request_id)
        chatImagesModel = chatImagesDomain.find_by_id(images_id=param.chat_images_id)
        if not chatImagesModel:
            logger.error("AmwayAIGC infer error, chatImagesModel is not empty, request_id={}, chat_images_id={}.", self.request_id, param.chat_images_id)
            raise BusinessException(ERROR_10910.code, ERROR_10910.message)
        client = FaceChainClient(request_id=self.request_id)
        try:
            result = client.infer(
                style=chatImagesModel.style,
                person_name=chatImagesModel.uuid,
                num_generate=chatImagesModel.num,
            )
        except BusinessException as e:
            chatImagesDomain.update(
                images_id=param.chat_images_id,
                images_status="fail_to_infer",
                images_uuid=chatImagesModel.uuid,
            )
            raise e
        # 保存推理后的图片至本地
        target_list = []
        for i, out_tmp in enumerate(result):
            file_name = chatImagesModel.uuid + "_" + f'{i}.png'
            file_path = os.path.join(chatImagesModel.dir, file_name)
            logger.info("AmwayAIGC infer info, request_id={}, file_path={}.", self.request_id, file_path)
            cv2.imwrite(file_path, np.array(out_tmp))
            target_list.append(file_path)
        # 更新图片生成状态
        chatImagesDomain.update(
            images_id=param.chat_images_id,
            images_status="infer",
            images_uuid=chatImagesModel.uuid,
            targets=target_list,
        )
        return target_list

