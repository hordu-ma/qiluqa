from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts import PromptTemplate

from custom.bespin.graphs.neo4j_response import ChatResponseVO
from models.llms.llms_adapter import LLMsAdapter


CYPHER_GENERATION_TEMPLATE = """
Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher statements for particular questions:
# How many people played in Top Gun?
MATCH (m:Movie {{title:"Top Gun"}})<-[:ACTED_IN]-()
RETURN count(*) AS numberOfActors

The question is:
{question}
"""

CYPHER_QA_TEMPLATE = """
You are an assistant that helps to form nice and human understandable answers.
The information part contains the provided information that you must use to construct an answer.
The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
Here is an example:

Question: Which managers own Neo4j stocks?
Context:[manager:CTL LLC, manager:JANE STREET GROUP LLC]
Helpful Answer: CTL LLC, JANE STREET GROUP LLC owns Neo4j stocks.

Follow this example when generating answers.
If the provided information is empty, say that you don't know the answer.
Information:
{context}

Question: {question}
Helpful Answer:
"""


class GraphNeo4jService:

    def __init__(
            self,
            is_direct_return: bool = False,
            is_middle_return: bool = False,
    ):
        self.graph = Neo4jGraph(url="bolt://47.236.254.2:7687", username="neo4j", password="Bspin2024")
        self.is_direct_return = is_direct_return
        self.is_middle_return = is_middle_return

    def call(self, ques) -> ChatResponseVO:
        CYPHER_GENERATION_PROMPT = PromptTemplate(
            input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
        )
        CYPHER_QA_PROMPT = PromptTemplate(
            input_variables=["context", "question"], template=CYPHER_QA_TEMPLATE
        )

        chain = GraphCypherQAChain.from_llm(
            llm=LLMsAdapter().get_model_instance(),
            graph=self.graph,
            cypher_prompt=CYPHER_GENERATION_PROMPT,
            qa_prompt=CYPHER_QA_PROMPT,
            verbose=True,
            validate_cypher=True,
            return_direct=self.is_direct_return,
            return_intermediate_steps=self.is_middle_return,
        )

        if self.is_middle_return:
            result = chain(ques)
            return ChatResponseVO(
                answer=result['result'],
                answer_list=result['intermediate_steps'],
            )
        else:
            result = chain.run(ques)
            return ChatResponseVO(
                answer=result if not self.is_direct_return else "",
                answer_list=result if self.is_direct_return else [],
            )
