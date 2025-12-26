from typing import List, Tuple
from langchain.schema import Document


class PrepareDocs:
    """
    预制知识库文档服务
    """
    def __init__(
            self,
            ques_docs: List[Tuple[Document, float]],
    ):
        """
        构造方法
        :param ques_docs: 知识库文档列表
        """
        self.ques_docs = ques_docs

    def get_new_ques_docs(self):
        """
        封装知识库文档列表
        :return: 知识库文档列表
        """
        if not self.ques_docs or len(self.ques_docs) == 0:
            return self.ques_docs

        return [
            (
                Document(
                    page_content=_page_content(_doc),
                    metadata=_doc.metadata,
                ),
                _score,
            )
            for _doc, _score in self.ques_docs
        ]


def _page_content(
        _doc: Document
) -> str:
    """
    封装文档信息格式
    :param _doc: 知识库文档
    :return: 文档信息
    """
    if _doc.metadata.get("answer"):
        return _doc.page_content + "\n" + _doc.metadata.get("answer")
        # return "问题：" + _doc.page_content + "\n" + "答案：" + _doc.metadata.get("answer")
    else:
        return _doc.page_content
