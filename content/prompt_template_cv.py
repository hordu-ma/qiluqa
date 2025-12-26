STUFF_PROMPT_INPUT_VARIABLES = ["question", "context"]
STUFF_PROMPT_TEMPLATE = """
使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。

{context}

问题: {question}
请按照以下格式回答问题，如:
answer:
1.
2.
3.
回答:"""

# STUFF_PROMPT_TEMPLATE = """
# 使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。
#
# {context}
#
# 问题: {question}
# 请按照以下格式回答问题，如:
# answer:
# 姓名:
# 性别:
# 年龄:
# 毕业于:
# 回答:"""

# STUFF_PROMPT_INPUT_VARIABLES = ["question", "context", "chat_history"]
# STUFF_PROMPT_TEMPLATE = """
# 使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。
#
# {context}
#
# {chat_history}
#
# 问题: {question}
# 请按照以下格式回答问题，如:
# answer:
# 1.
# 2.
# 3.
# 回答:
# """

REFINE_PROMPT_INPUT_VARIABLES = ["question", "existing_answer", "context_str"]
REFINE_INPUT_TEMPLATE = """
原问题如下: {question}
我们已经提供了一个现有的答案: {existing_answer}
我们有机会（仅在必要时）通过下面的更多上下文来完善现有答案。
------------
{context_str}
------------
在新的背景下，完善原始答案以更好地回答问题。
如果上下文没有用处，则返回原始答案。
"""


REFINE_PROMPT_QUEST_VARIABLES = ["context_str", "question"]
REFINE_QUEST_TEMPLATE = """
上下文信息如下。
---------------------
"{context_str}
---------------------
给定上下文信息而不是先验知识。
请按照以下格式回答问题，如:
answer:
姓名：
性别：
年龄：
毕业于：
回答以下问题: {question}
"""