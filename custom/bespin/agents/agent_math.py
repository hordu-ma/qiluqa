from typing import Any

from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import BaseTool

from models.llms.llms_adapter import LLMsAdapter


class EvaluateMathTool(BaseTool):

    name = "计算器"
    description = "这是一个计算器"

    def _run(self, expr: str, *args: Any, **kwargs: Any) -> Any:
        return eval(expr)


if __name__ == "__main__":
    tools = [EvaluateMathTool()]
    agent = create_react_agent(
        llm=LLMsAdapter(model="DashScope", model_name="qwen-max").get_model_instance(),
        tools=tools,
        prompt=hub.pull("hwchase17/openai-functions-agent")
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools)
    agent_executor.invoke({"input": "帮我计算一下 (4 * 4 + 0.5) / 2  的结果是多少？"})

