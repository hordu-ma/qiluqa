import re
import os
import uuid
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime, date
from loguru import logger
from config.base_config import SPIDER_FILE_PATH
from framework.business_code import ERROR_10001, ERROR_10210, ERROR_10207
from framework.business_except import BusinessException
from models.embeddings.es_model_adapter import EmbeddingsModelAdapter
from models.vectordatabase.v_client import get_instance_client
from langchain.docstore.document import Document
from service.domain.ai_namespace import AiNamespaceDomain, NamespaceModel
from service.domain.ai_namespace_file_image import AiNamespaceFileImageDomain
from service.domain.ai_namespace_file import AiNamespaceFileDomain, NamespaceFileModel
from service.domain.ai_namespace_network import NameSpaceNetworkModel, AiNamespaceNetworkDomain
from service.namespacefile.namespace_file_metadata import MetadataModel
from service.namespacefile.namespace_file_request import ChunkPageParam, ChunkFileStatusParam, \
    ModifyChunkParam, SpiderUrlParam
from service.namespacefile.namespace_file_response import (
    ChunkPageResponse,
    ChunkPageResponseVO,
    ChunkPageEmbeddingResponseVO
)
from service.schedule.namespace_file_schedule import handle


class NamespaceFileService:
    """
    知识库文件服务
    """

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def query_chunk_page(
            self,
            param: ChunkPageParam,
            namespace_id: str,
    ) -> ChunkPageResponse:
        """
        分片分页查询
        :param param: 分页参数
        :param namespace_id: 知识库标识
        :return: 分片列表
        """
        if param.file_id:
            namespaceFileModel = AiNamespaceFileDomain(request_id=self.request_id).find_by_id(file_id=param.file_id)
            if not namespaceFileModel:
                logger.error("###API###query_chunk_page ERROR, [{}]未查询到知识库文件[{}]信息, request_id={}.",
                             ERROR_10210, param.file_id, self.request_id)
                raise BusinessException(ERROR_10210.code, ERROR_10210.message)
            if namespace_id != namespaceFileModel.namespace_id:
                logger.error("###API###query_chunk_page ERROR, [{}]指定文件[{}]所属知识库标识不匹配, request_id={}.",
                             ERROR_10207, param.file_id, self.request_id)
                raise BusinessException(ERROR_10207.code, ERROR_10207.message)
            if namespaceFileModel.vector_status in ('None', 'Wait'):
                return ChunkPageResponse(
                    data=ChunkPageResponseVO(
                        page_nums=param.page_nums,
                        page_size=param.page_size,
                        page_total=0,
                        chunk_list=[],
                    )
                )
        # 查询文件所属知识库信息
        namespaceModel = AiNamespaceDomain(request_id=self.request_id).find_by_id(namespace_id)
        if not namespaceModel:
            logger.error("###query_chunk_page ERROR, [{}]未查询到所属知识库[{}]信息, request_id={}.", ERROR_10001,
                         namespace_id, self.request_id)
            raise BusinessException(ERROR_10001.code, ERROR_10001.message)

        vector_list, vector_count = get_instance_client().query_page_data(
            namespace=namespaceModel.namespace,
            ids=param.ids,
            document=param.content,
            page_nums=int(param.page_nums),
            page_size=int(param.page_size),
            file_id=param.file_id if param.file_id else None,
            status=param.status if param.status else None,
        )

        chunk_list = []
        for v in vector_list:
            logger.info("###query_chunk_page INFO, Current chunk info=[file_id={}, create_date={}, update_date={}].",
                        v.file_id, v.create_date, v.update_date)
            document_text = v.document
            chunk_label = ""
            if v.cmetadata.get('images'):
                for image_id in v.cmetadata['images']:
                    image_data = (AiNamespaceFileImageDomain(request_id=self.request_id)
                                  .find_by_image_id(image_id=image_id))
                    if image_data:
                        data_src = image_data.path + image_data.image_id + image_data.type
                        img_path = f'<img src="{data_src}" imageid="{image_id}">'
                        document_text = document_text.replace(image_id, img_path)
            if v.cmetadata.get("chunk_label"):
                chunk_label = v.cmetadata["chunk_label"]
            chunk_list.append(ChunkPageEmbeddingResponseVO(
                uuid=str(v.uuid),
                collection_id=str(v.collection_id),
                custom_id=v.custom_id,
                document=document_text,
                metadata=v.cmetadata,
                file_id=(v.file_id if v.file_id else ""),
                create_date=(v.create_date if v.create_date else datetime.now()),
                update_date=(v.update_date if v.update_date else datetime.now()),
                number=v.number,
                status=v.status,
                document_len=len(v.document),
                chunk_label=chunk_label
            ))

        return ChunkPageResponse(
            data=ChunkPageResponseVO(
                page_nums=str(param.page_nums),
                page_size=str(param.page_size),
                page_total=str(vector_count),
                chunk_list=chunk_list,
            )
        )

    def modify_chunk(self, param: ModifyChunkParam):
        """
        编辑分片
        :param param: 业务参数
        :return: 执行结果
        """
        document_text, document, image_id_list = self.get_document_info(param=param)
        metadataModel = MetadataModel(
            source=param.metadata.source,
            answer=param.metadata.answer,
            scene=param.metadata.scene,
            name=param.metadata.name,
            images=image_id_list,
            chunk_label=param.chunkLabel,
        )
        vectorClient = get_instance_client()
        vectorClient.update_data(
            custom_id=param.customId,
            document=document,
            document_text=document_text,
            namespace=param.namespace,
            metadataModel=metadataModel,
            embedding=EmbeddingsModelAdapter().get_model_instance()
        )

    def insert_chunk(self, param: ModifyChunkParam):
        """
        新增分片
        :param param: 业务参数
        :return: 执行结果
        """
        document_text, document, image_id_list = self.get_document_info(param=param)
        metadataModel = MetadataModel(
            source=param.metadata.source,
            answer=param.metadata.answer,
            scene=param.metadata.scene,
            name=param.metadata.name,
            images=image_id_list,
            chunk_label=param.chunkLabel
        )
        vectorClient = get_instance_client()
        custom_id = vectorClient.insert_data(
            file_id=param.fileId,
            document=document,
            document_text=document_text,
            namespace=param.namespace,
            metadataModel=metadataModel,
            embedding=EmbeddingsModelAdapter().get_model_instance()
        )
        AiNamespaceFileDomain(self.request_id).update_vector_ids(custom_id=custom_id, file_id=param.fileId)

    def change_status_by_file_id_list(
            self,
            param: ChunkFileStatusParam
    ):
        file_id_list = param.file_id_list
        status_tag = param.status_tag
        if file_id_list:
            vectorClient = get_instance_client()
            vectorClient.change_vector_status(file_id_list=file_id_list, status_tag=status_tag)
        logger.info("###search_chunk_ids INFO, file_id_list={}, len_file_id_list={}, request_id={}.",
                    file_id_list, len(file_id_list), self.request_id)

    def change_status_by_custom_id_list(
            self,
            custom_id_list: list[str],
            status_tag: str
    ):
        """
        以分片ID列表更改分片状态
        """
        vectorClient = get_instance_client()
        vectorClient.change_vector_status(custom_id_list=custom_id_list, status_tag=status_tag)
        logger.info("###search_chunk_ids INFO, custom_id_list={}, len_column_id_list={}, request_id={}.",
                    custom_id_list, len(custom_id_list), self.request_id)

    def get_document_info(
            self,
            param: ModifyChunkParam
    ):
        document_text = ""
        imageId = []
        document = param.document
        document = document.replace("<p>", "")
        document = document.replace("</p>", "\n")
        imagePattern = r'<img\s+[^>]+>'
        imageIdPattern = r'IMAGE\d+'
        imageMatch = re.findall(imagePattern, str(document))
        for i in range(len(imageMatch)):
            imageIdMatch = re.search(imageIdPattern, imageMatch[i])
            imageId.append(imageIdMatch.group(0))
            document_text = document.replace(imageMatch[i], "")
            document = document.replace(imageMatch[i], imageIdMatch[i])
        logger.info("###insert_chunk INFO, document_info={},request_id={}.", document, self.request_id)
        return document_text, document, imageId

    def get_spider_url_info(
            self,
            network_model: NameSpaceNetworkModel,
            url: str,
            is_first_spider: bool = True,
            path: str = None,
            filename: str = None
    ):
        try:
            response = urllib.request.urlopen(url=url)
            text_content = BeautifulSoup(response.read(), 'html.parser')
            if is_first_spider:
                today_date = date.today()
                today_date = str(today_date).replace('-', '')
                filename = self.request_id.replace('-', '') + '.html'
                filename_path = SPIDER_FILE_PATH.format(namespace_id=network_model.namespace_id, today_date=today_date,
                                                        file_name=filename)
                path = filename_path.replace(filename, "")
                os.makedirs(os.path.dirname(path), exist_ok=True)
            else:
                filename_path = path + filename
            with open(filename_path, 'w', encoding='utf-8') as f:
                f.write(str(text_content))
            logger.info("###get_spider_url INFO, url_filename={},request_id={}.", filename, self.request_id)
            return text_content, filename, path, filename_path
        except Exception as e:
            logger.error(e)
            return False

    def create_spider_url_info(
            self,
            network_model: NameSpaceNetworkModel,
            param: SpiderUrlParam
    ):
        text_content, filename, path, filename_path = self.get_spider_url_info(network_model=network_model,
                                                                               url=param.url)
        AiNamespaceNetworkDomain(self.request_id).set_network_file_id(
            file_id=param.file_id,
            network_model=network_model
        )
        title = text_content.title.string
        if title:
            title = title + '.html'
        if AiNamespaceFileDomain(request_id=self.request_id).insert(
                namespace_id=param.namespace_id,
                file_id=param.file_id,
                creator=network_model.creator,
                trace_name=title,
                name=filename,
                display_name=title,
                path=path,
                type='html',
                size=os.path.getsize(filename_path)
        ):
            return True
        else:
            return False

    def update_spider_url_info(
            self,
            network_model: NameSpaceNetworkModel,
            url: str,
            filename: str,
            path: str
    ):
        """
        更新网页爬取功能定时轮询信息
        更新数据库信息
        """
        try:
            if path and filename:
                self.get_spider_url_info(
                    network_model=network_model,
                    url=url,
                    filename=filename,
                    path=path,
                    is_first_spider=False
                )
            else:
                self.get_spider_url_info(
                    network_model=network_model,
                    url=url,
                    filename=filename,
                    path=path,
                    is_first_spider=True
                )
            self.update_spider_file_data(network_model=network_model)
            return True
        except Exception as e:
            logger.error(e)
            return False

    def update_spider_file_data(
            self,
            network_model: NameSpaceNetworkModel,
    ):
        try:
            namespaceFileDomain = AiNamespaceFileDomain(request_id=self.request_id)
            namespaceFileModel = namespaceFileDomain.find_by_id(file_id=network_model.file_id)
            namespaceModel = AiNamespaceDomain(request_id=self.request_id).find_by_id(
                namespace_id=network_model.namespace_id)
            get_instance_client().delete_file_data(namespace=namespaceModel.namespace,
                                                   file_id_list=[network_model.file_id])
            namespaceFileDomain.update(
                file_id=int(namespaceFileModel.id),
                vector_ids=[],
                vector_status='Wait',
                vector_count=0,
                deleted=0
            )
            handle(
                namespaceFileModel=namespaceFileModel,
                namespaceFileDomain=namespaceFileDomain,
                request_id=self.request_id
            )
        except Exception as e:
            logger.error(e)
            return False

