import uuid
from typing import List, Tuple
import pandas as pd
from langchain.schema import Document
from loguru import logger
from custom.amway.prepare.service.prepare_update_param import PrepareUpdateParam, PrepareData
from framework.business_code import ERROR_10206, ERROR_10001, ERROR_10209, ERROR_10210
from framework.business_except import BusinessException
from models.embeddings.es_model_adapter import EmbeddingsModelAdapter
from models.vectordatabase.v_client import get_instance_client
from service.domain.ai_namespace import NamespaceModel, AiNamespaceDomain
from service.domain.ai_namespace_file import AiNamespaceFileDomain


class NamespacePrepare:
    """
    知识库预制化服务
    """
    def __init__(
            self,
            path: str,
            file_type: str,
            file_path: str,
            file_name: str,
            file_size: int,
            namespace_id: str,
            encoding: str = "UTF-8",
            split_len: int = 1000,
            scene: str = None,
            data_list: List[Tuple] = None,
            remark: str = None,
            request_id: str = str(uuid.uuid4()),
    ):
        self.path = path
        self.file_type = file_type
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.namespace_id = namespace_id
        self.encoding = encoding
        self.split_len = split_len
        self.scene = scene
        self.data_list = data_list
        self.remark = remark
        self.request_id = request_id

    def transformer(self):
        """
        预制文件转向量化处理
        :return: None
        """
        param = PrepareUpdateParam()
        if self.scene and self.scene == 'insert':
            for a in self.data_list:
                qa = PrepareData(
                    question=a[0],
                    answer=a[1] if len(a) >= 2 else None,
                    scene=a[2] if len(a) >= 3 else None,
                )
                param.insert_list.append(qa)
        else:
            data = self.loader()
            for row in data.values:
                if str(row[0]) == 'nan' or str(row[1]) == 'nan':
                    continue
                qa = PrepareData(
                    question=row[0],
                    answer=row[1] if len(row) >= 2 else None,
                    scene=row[2] if len(row) >= 3 and str(row[2]) != 'nan' else None,
                )
                param.update_list.append(qa)
        NamespacePrepareService(
            param=param,
            namespace_id=self.namespace_id,
            name=self.file_name,
            path=self.path,
            file_path=self.file_path,
            type=self.file_type,
            size=str(self.file_size),
            remark=self.remark if self.remark else self.file_name,
            request_id=self.request_id
        ).handle()

    def loader(self):
        try:
            return pd.read_csv(self.file_path, encoding=self.encoding)
        except Exception as err:
            print(err)
            logger.error("######NamespacePrepare error, loader csv fail, message={}", err)
            raise BusinessException(ERROR_10206.code, ERROR_10206.message)


class NamespacePrepareService:

    def __init__(
            self,
            param: PrepareUpdateParam,
            namespace_id: str,
            name: str = "",
            path: str = "",
            file_id: str = None,
            file_path: str = "",
            type: str = "",
            size: str = "0",
            remark: str = "",
            file_display_name: str = "",
            request_id: str = str(uuid.uuid4()),
    ):
        self.param = param
        self.namespace_id = namespace_id
        self.name = name
        self.path = path
        self.file_id = file_id
        self.file_path = file_path
        self.type = type
        self.size = size
        self.remark = remark
        self.file_display_name = file_display_name
        self.request_id = request_id

    def handle(self):
        # 查询指定知识库
        namespaceModel = AiNamespaceDomain(request_id=self.request_id).find_by_id(namespace_id=self.namespace_id)
        if not namespaceModel:
            logger.error("NamespacePrepareService ERROR, [{}]未查询到所属知识库[{}]信息, request_id={}.", ERROR_10001, self.namespace_id, self.request_id)
            raise BusinessException(ERROR_10001.code, ERROR_10001.message)
        if self.file_id:
            return self.handle_by_file_id(namespaceModel=namespaceModel)

        # 查询知识库所属文件清单
        file_list = AiNamespaceFileDomain(request_id=self.request_id).find_by_condition(namespace_id=self.namespace_id)
        # 处理需要删除的向量数据
        if self.param.delete_list and len(self.param.delete_list) > 0:
            # 删除向量数据
            vector_client = get_instance_client()
            vector_client.delete_data(namespace=namespaceModel.namespace, ids=self.param.delete_list)
            # 更新业务数据
            for namespaceFileModel in file_list:
                ids_model = str(namespaceFileModel.vector_ids).split(',') if namespaceFileModel.vector_ids else []
                ids_array = [i for i in ids_model if i not in self.param.delete_list]
                # 更新业务数据
                AiNamespaceFileDomain(request_id=self.request_id).update(
                    file_id=int(namespaceFileModel.id),
                    vector_ids=ids_array,
                    vector_status='Done',
                    vector_count=0,
                    deleted=1 if len(ids_array) == 0 else 0,
                )
        # 处理需要更新的向量数据
        if self.param.update_list and len(self.param.update_list) > 0:
            ques_list = [q.question for q in self.param.update_list]
            for namespaceFileModel in file_list:
                vector_client = get_instance_client()
                # 查询向量数据
                ids_model = str(namespaceFileModel.vector_ids).split(',') if namespaceFileModel.vector_ids else []
                vector_data_list = vector_client.query_data(namespace=namespaceModel.namespace, ids=ids_model)
                ids_array = [i.custom_id for i in vector_data_list if i.document not in ques_list]
                del_array = [i.custom_id for i in vector_data_list if i.custom_id not in ids_array]
                # 删除向量数据
                vector_client.delete_data(namespace=namespaceModel.namespace, ids=del_array)
                # 更新业务数据
                AiNamespaceFileDomain(request_id=self.request_id).update(
                    file_id=int(namespaceFileModel.id),
                    vector_ids=ids_array,
                    vector_status='Done',
                    vector_count=0,
                    deleted=1 if len(ids_array) == 0 else 0,
                )
            self.param.insert_list = self.param.insert_list + self.param.update_list
        # 处理需要新增的向量数据
        if self.param.insert_list and len(self.param.insert_list) > 0:
            docs = []
            for p in self.param.insert_list:
                metadata = {
                    "source": self.file_path,
                    "answer": p.answer,
                    "scene": p.scene,
                }
                document = Document(page_content=p.question, metadata=metadata)
                docs.append(document)
            logger.info("####向量化的文档列表有：{}.", len(docs))
            # 保存向量数据
            ids = get_instance_client().insert_data_list(
                split_docs=docs,
                embedding=EmbeddingsModelAdapter().get_model_instance(),
                namespace=namespaceModel.namespace
            )
            logger.info("####切割后的文件ids有：{}.", len(ids))
            # 保存文件信息
            namespaceFileDomain = AiNamespaceFileDomain()
            namespaceFileDomain.create(
                namespace_id=self.namespace_id,
                name=self.name,
                path=self.path,
                type=self.type,
                size=self.size,
                display_name=self.file_display_name,
                remark=self.remark,
                vector_ids=ids,
            )

    def handle_by_file_id(self, namespaceModel: NamespaceModel):
        if not self.file_id:
            logger.error("NamespacePrepareService ERROR, [{}]知识库文件标识不能为空, request_id={}.", ERROR_10209, self.request_id)
            raise BusinessException(ERROR_10209.code, ERROR_10209.message)

        namespaceFileModel = AiNamespaceFileDomain(request_id=self.request_id).find_by_id(file_id=self.file_id)
        if not namespaceFileModel:
            logger.error("NamespacePrepareService ERROR, [{}]未查询到知识库文件信息[{}], request_id={}.", ERROR_10210, self.file_id, self.request_id)
            raise BusinessException(ERROR_10210.code, ERROR_10210.message)

        ids_model = str(namespaceFileModel.vector_ids).split(',') if namespaceFileModel.vector_ids else []
        # 处理需要删除的向量数据
        if self.param.delete_list and len(self.param.delete_list) > 0:
            ids_delete_list = [i for i in ids_model if i in self.param.delete_list]
            ids_update_list = [i for i in ids_model if i not in ids_delete_list]
            # 删除向量数据
            vector_client = get_instance_client()
            vector_client.delete_data(namespace=namespaceModel.namespace, ids=ids_delete_list)
            # 更新业务数据
            AiNamespaceFileDomain(request_id=self.request_id).update(
                file_id=int(namespaceFileModel.id),
                vector_ids=ids_update_list,
                vector_status='Done',
                vector_count=0,
                deleted=0 if len(ids_update_list) > 0 else 1,
            )
            ids_model = ids_update_list
        # 处理需要更新的向量数据
        if self.param.update_list and len(self.param.update_list) > 0:
            ques_list = [q.question for q in self.param.update_list]
            # 查询向量数据
            vector_client = get_instance_client()
            vector_data_list = vector_client.query_data(namespace=namespaceModel.namespace, ids=ids_model)
            que_update_list = [i.document for i in vector_data_list if i.document in ques_list]
            ids_delete_list = [i.custom_id for i in vector_data_list if i.document in ques_list]
            ids_update_list = [i.custom_id for i in vector_data_list if i.custom_id not in ids_delete_list]
            # 删除向量数据
            vector_client.delete_data(namespace=namespaceModel.namespace, ids=ids_delete_list)
            # 更新业务数据
            AiNamespaceFileDomain(request_id=self.request_id).update(
                file_id=int(namespaceFileModel.id),
                vector_ids=ids_update_list,
                vector_status='Done',
                vector_count=0,
                deleted=0 if len(ids_update_list) > 0 else 1,
            )
            ids_model = ids_update_list
            update_list = [u for u in self.param.update_list if u.question in que_update_list]
            self.param.insert_list = self.param.insert_list + update_list
        # 处理需要新增的向量数据
        if self.param.insert_list and len(self.param.insert_list) > 0:
            docs = []
            for p in self.param.insert_list:
                metadata = {
                    "source": self.file_path,
                    "answer": p.answer,
                    "scene": p.scene,
                }
                document = Document(page_content=p.question, metadata=metadata)
                docs.append(document)
            logger.info("####向量化的文档列表有：{}.", len(docs))
            # 保存向量数据
            ids = get_instance_client().insert_data_list(
                split_docs=docs,
                embedding=EmbeddingsModelAdapter().get_model_instance(),
                namespace=namespaceModel.namespace
            )
            ids_update_list = ids_model + ids
            logger.info("####切割后的文件ids有：{}.", len(ids))
            # 更新业务数据
            AiNamespaceFileDomain(request_id=self.request_id).update(
                file_id=int(namespaceFileModel.id),
                vector_ids=ids_update_list,
                vector_status='Done',
                vector_count=0,
                deleted=0 if len(ids_update_list) > 0 else 1,
            )
