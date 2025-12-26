# 文本摘要提示词
import uuid
from typing import List
from custom.amway.amway_config import SFT_OUTLINE_SPLIT

####################
####################
# 文本摘要提示词
prompt_template_abstract = """
原问题如下: {question}

我们已经提供了一个现有的文本摘要: {existing_answer}
我们有机会（仅在必要时）通过下面的更多上下文来完善现有文本摘要。
------------
{context_str}
------------

在新的背景下，完善原始答案以更好地回答问题。
如果上下文没有用处，则返回原始答案。
"""
# 文本摘要提示词占位符
prompt_template_abstract_variables = ["question", "existing_answer", "context_str"]

# 文本摘要提示词
prefix_prompt_template_abstract = """
上下文信息如下。
---------------------
"{context_str}
---------------------
给定上下文信息而不是先验知识。

回答以下问题: {question}

Answer:
"""
# 文本摘要提示词占位符
prefix_prompt_template_abstract_variables = ["context_str", "question"]


####################
####################
# 文本大纲提示词
prompt_template_outline = """
原问题如下: {question}

我们已经提供了一个现有的文本大纲: {existing_answer}
我们有机会（仅在必要时）通过下面的更多上下文来完善现有文本大纲。
------------
{context_str}
------------

在新的背景下，完善原始答案以更好地回答问题。
如果上下文没有用处，则返回原始答案。

请按照以下格式回答问题，如:
- aaa
- bbb
- ccc
"""
# 文本大纲提示词占位符
prompt_template_outline_variables = ["question", "existing_answer", "context_str"]

# 文本大纲提示词
prefix_prompt_template_outline = """
上下文信息如下。
---------------------
"{context_str}
---------------------
给定上下文信息而不是先验知识。
请按照以下格式回答问题，如:
- aaa
- bbb
- ccc

回答以下问题: {question}

Answer:
"""
# 文本大纲提示词占位符
prefix_prompt_template_outline_variables = ["context_str", "question"]


####################
####################
# 文本段落提示词
prompt_template_paragraph = """
原问题如下: {question}

我们已经提供了一个现有的答案: {existing_answer}
我们有机会（仅在必要时）通过下面的更多上下文来完善现有答案。
------------
{context_str}
------------

在新的背景下，完善原始答案以更好地回答问题。
如果上下文没有用处，则返回原始答案。
"""
# 文本段落提示词占位符
prompt_template_paragraph_variables = ["question", "existing_answer", "context_str"]

# 文本段落提示词
prefix_prompt_template_paragraph = """
上下文信息如下。
---------------------
"{context_str}
---------------------
给定上下文信息而不是先验知识。

回答以下问题: {question}

Answer:
"""
# 文本段落提示词占位符
prefix_prompt_template_paragraph_variables = ["context_str", "question"]


def split_file_metadata(metadata: dict) -> str:
    """
    切分文件元数据中的关键信息
    :param metadata: 元数据
    :return: 关键信息
    """
    _file_name = ""
    if "source" in metadata:
        _source_file_path = metadata["source"]
        if "\\" in _source_file_path:
            _file_name = _source_file_path.split("\\")[::-1][0]
        elif "/" in _source_file_path:
            _file_name = _source_file_path.split("/")[::-1][0]
    # 没有元数据信息场景
    if len(_file_name) == 0:
        _file_name = str(uuid.uuid4())
        return _file_name + ".json"
    # 忽略后缀信息
    return _file_name.split('.')[0] + ".json"


def split_answer(answer: str) -> str:
    """
    AI回答前缀信息处理
    :param answer: AI回答信息
    :return: 截取prefix后的answer
    """
    if "Answer: " in answer:
        return answer.split("Answer:")[1]
    return answer


def split_outline(answer: str) -> List[str]:
    """
    大纲信息切割处理
    :param answer: AI回答信息
    :return: 大纲信息
    """
    array = answer.split(SFT_OUTLINE_SPLIT)
    if array and len(array) > 1:
        return [arr.strip() for arr in array if len(arr.strip()) > 5]
    return []
