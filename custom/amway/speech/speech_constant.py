speech_template = """我想让你充当演讲稿生成专家，我会提供演讲稿的'业务背景','风格背景','底稿模板'，而您的工作是根据具体问题生成演讲稿，并根据'业务背景','风格背景','底稿模板'完善内容。

业务背景: 
{content_business}

风格背景: 
{content_style}

底稿模板: 
{content_draft}

格式要求: 
{condition}

{chat_history}
问题要求: {question}
AI:
"""

speech_history_key = "chat_history"
speech_input_key = "question"
speech_variables = [speech_history_key, speech_input_key]

speech_condition = """
1.要有'开场白'和'结束总结'的内容.
"""
