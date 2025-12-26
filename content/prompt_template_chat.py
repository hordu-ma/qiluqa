CONVERSATION_CHAT_TEMPLATE = """
The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.

Current conversation:
{chat_history}
Human: {question}
AI:
"""
MEMORY_HISTORY_KEY = "chat_history"
MEMORY_INPUT_KEY = "question"
CONVERSATION_CHAT_VARIABLES = [MEMORY_HISTORY_KEY, MEMORY_INPUT_KEY]

