from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_community.tools import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function

from config.base_config import TAVILY_API_KEY
from models.chatai.deepseek.chat_deepseek import ChatDeepseekAI

if __name__ == "__main__":
    search = TavilySearchResults(max_results=2, tavily_api_key=TAVILY_API_KEY, name="Tavily")
    # 定义提示模板
    config = {"configurable": {"thread_id": "abc123"}}
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are very powerful assistant, but bad at calculating lengths of words.",
            ),
            MessagesPlaceholder(variable_name='chat_history'),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    tools = [search]
    # 创建代理
    #llm = ChatOpenAI(api_key=BASHSCOPE_API_KEY, base_url=BASHSCOPE_BASE_URL, model=BASHSCOPE_MODEL_NAME, streaming=True)
    #llm = ChatDashScopeAI(streaming=True)
    llm = ChatDeepseekAI(streaming=True)
    llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in tools])
    agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
                "chat_history": lambda x: x["chat_history"],
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
    )

    # 创建代理执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )
    # 执行查询
    stream_response = agent_executor.stream({"input": "今天广州天气", "chat_history": []}, config)
    for chunk in stream_response:
        print(chunk, end='', flush=True)
        print()  # 换行
