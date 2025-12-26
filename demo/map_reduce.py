import json

from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader

from models.llms.dashscope.dashscope import DashScopeAI


# 映射链 - 累积拼接版本
def get_content(llm, docs, question, word_limit=1024):
    # 设置映射阶段的提示模板
    map_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个信息抽取专家。请根据已有内容和新文本抽取关键信息，总长度不超过{word_limit}字。用户需求：{question}"),
        ("human", "已有内容：{existing_content}\n\n新内容：{text}"),
    ])
    # 初始化累积内容
    existing_content = ""
    # 依次处理每个文档块
    for doc in docs:
        # 调用模型进行映射
        inputs = {
            "existing_content": existing_content,
            "text": doc.page_content,
            "question": question,
            "word_limit": word_limit
        }
        # 生成新的累积内容
        chain = map_prompt | llm | StrOutputParser()
        new_content = chain.invoke(inputs)
        existing_content = new_content
    return existing_content


def run():
    # 初始化模型
    llm = DashScopeAI()
    # 设置归约阶段的提示模板
    reduce_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个总结专家。用户需求：{question}"),
        ("human", "{texts}"),
    ])
    # 归约链
    reduce_chain = (
            RunnablePassthrough()
            | (lambda x: {
        "texts": x["final_content"],
        "question": x["question"]
    })
            | reduce_prompt
            | llm
            | StrOutputParser()
    )
    # 完整的 MapReduce链
    map_reduce_chain = (
            RunnablePassthrough()
            | (lambda x: {
        "final_content": get_content(
            llm=llm,
            docs=x["docs"],
            question=x["question"],
            word_limit=1024
        ),
        "question": x["question"]
    })
            | reduce_chain
    )
    # 示例文档
    document = TextLoader("example.txt", encoding="utf-8").load()[0]
    # 文本分块器
    text_splitter = CharacterTextSplitter(chunk_size=1024, chunk_overlap=50)
    split_docs = text_splitter.split_documents([document])
    # 运行链
    results = map_reduce_chain.stream({"docs": split_docs, "question": "请用100字总结这段话"})
    result = ""
    for chunk in results:
        result += json.loads(str(chunk)).get("content")
    return result


if __name__ == '__main__':
    print("result:", run())
