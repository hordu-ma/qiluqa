import asyncio

from langchain.agents import AgentExecutor, \
    create_tool_calling_agent
from langchain_community.tools import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.base_config import TAVILY_API_KEY
from models.chatai.dashscope.chat_dashscop import ChatDashScopeAI
from models.chatai.deepseek.chat_deepseek import ChatDeepseekAI


# **核心：自定义流式输出逻辑**
async def run_agent_with_streaming():
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
    # llm = ChatOpenAI(api_key=BASHSCOPE_API_KEY, base_url=BASHSCOPE_BASE_URL, model=BASHSCOPE_MODEL_NAME, streaming=True)
    llm = ChatDashScopeAI(streaming=True)
    # llm = ChatDeepseekAI(streaming=True)
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        max_iterations=3,
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    # 使用 astream_events 获取细粒度事件流
    async for event in agent_executor.astream_events({"input": "docker 是什么？", "chat_history": []}, version="v2"):
        print("event=", event)
        kind = event["event"]
        # 1. LLM 开始生成文本（逐字输出）
        if kind == "on_chat_model_stream":
            is_thinking = event["data"]["chunk"].response_metadata.get("is_thinking", False)
            is_answer = event["data"]["chunk"].response_metadata.get("is_answer", False)
            content = event["data"]["chunk"].content
            if content:  # 过滤空内容
                print(content, end="", flush=True)
        # 2. 代理决定调用工具（显示加载状态）
        elif kind == "on_tool_start":
            tool_name = event["name"]
            print(f"\n\n[正在调用工具: {tool_name}]...", end="", flush=True)
        # 3. 工具返回结果后继续流式输出
        elif kind == "on_tool_end":
            output = event["data"]["output"]
            print(f"\n[工具返回]: {output}\n", end="", flush=True)


if __name__ == "__main__":
    asyncio.run(run_agent_with_streaming())
    # llm = DashScopeAI(streaming=True)
    # stream = llm.stream("今天平南的天气如何")
    # for event in stream:
    #     print(event)
