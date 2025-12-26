import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from loguru import logger

from config.base_config_dashscope import BASHSCOPE_MODEL_NAME
from models.llms.llms_adapter import LLMsAdapter

"""
文件分块大小
"""
CHUNK_SIZE = 1024 * 20


class MapReduceSummarizer:
    def __init__(self, model: str = "DashScope", model_name: str = BASHSCOPE_MODEL_NAME):
        # self.llm = LLMsAdapter(model=model, model_name=model_name).get_model_instance()
        self.llm = LLMsAdapter(model=model, model_name=model_name).get_chat_model_instance(history=[])

    def process_single_file(self, file, word_limit, question):
        """
        处理单个文件的方法
        """
        # 设置映射阶段的提示模板
        map_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "你是一个信息抽取专家。请根据已有内容和新文本内容抽取关键信息，总长度不超过{word_limit}字。用户需求：{question}"),
            ("human", "已有内容：{existing_content}\n\n新文本内容：{text}"),
        ])
        # 初始化累积内容
        existing_content = ""
        try:
            document = TextLoader(file["filePath"], encoding="utf-8").load()[0]

            if len(document.page_content) <= CHUNK_SIZE:
                return {"fileName": file["fileName"], "content": document.page_content}

            # 文本分块器
            text_splitter = CharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=100)
            split_docs = text_splitter.split_documents([document])

            # 依次处理每个文档块
            for doc in split_docs:
                # 调用模型进行映射
                inputs = {
                    "existing_content": existing_content,
                    "text": doc.page_content,
                    "question": question,
                    "word_limit": word_limit
                }
                # 生成新的累积内容
                chain = map_prompt | self.llm | StrOutputParser()
                new_content = chain.invoke(inputs)
                existing_content = new_content
        except Exception as err:
            logger.error("###API###MapReduceSummarizer get_content error, err={}.", err)
        return {"fileName": file["fileName"], "content": existing_content}

    def get_content(self, word_limit=1024 * 5, files: List[Dict] = None, question: str = None, max_workers: int = 4):
        """
        并行处理所有文件，最后统一汇总结果输出
        """
        if not files:
            return []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_single_file, file, word_limit, question) for file in files]
            results = [future.result() for future in futures]
        return results

    def run(self, files: List[Dict] = None, question: str = None, word_limit: int = 1024 * 8, max_workers: int = 4):
        """
        遍历处理所有文件，逐个文件进行分快处理，按顺序将分块分别进行summary
        将上一次的summary结果existing_content，与下一个分块内容text合并再进行下一轮的summary，以此类推，直到处理完所有文件的所有分片
        最后对最后总结的结果进行最后一轮推理
        :param word_limit: 每次summary输出最大字数限制
        :param question: 自定义问题
        :param files: 文件信息
        :param max_workers: 最大并发数
        :return:
        """
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
                | self.llm
                | StrOutputParser()
        )
        # 完整的 MapReduce链
        map_reduce_chain = (
                RunnablePassthrough()
                | (lambda x: {
            "final_content": self.get_content(word_limit=word_limit, files=files, question=question, max_workers=max_workers),
            "question": x["question"]
        })
                | reduce_chain
        )
        # 运行链
        results = map_reduce_chain.stream({"question": question})
        result = ""
        for chunk in results:
            result += json.loads(str(chunk)).get("content")
        return result


if __name__ == '__main__':
    start_time = time.time()
    # files = [{"fileName": "example.txt", "filePath": "../demo/example.txt"}, {"fileName": "example1.txt", "filePath": "../demo/example1.txt"},
    #          {"fileName": "example2.txt", "filePath": "../demo/example2.txt"}, {"fileName": "example3.txt", "filePath": "../demo/example3.txt"}]
    files = [{"fileName": "example.txt", "filePath": "../demo/example.txt"}]
    question = "请总结关键信息，不要丢失信息点"
    summarizer = MapReduceSummarizer()
    print("result:", summarizer.get_content(files=files, question=question, max_workers=4))
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"代码执行耗时: {elapsed_time:.2f} 秒")