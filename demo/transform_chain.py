from langchain.chains import TransformChain
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models.llms.dashscope.dashscope import DashScopeAI

with open("example.txt", encoding="utf-8") as f:
    novel_text = f.read()


# pip install transformers
# 安装 PyTorch（推荐，大多数 NLP 模型都支持） pip install torch
# 或者安装 TensorFlow pip install tensorflow
# 定义文本摘要转换函数
def transform_func(inputs: dict) -> dict:
    text = inputs["raw_text"]
    print(f"文本长度: {len(text)} 字符")
    # 文本分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    docs = text_splitter.create_documents([text])
    summary_chain = load_summarize_chain(
        DashScopeAI(),
        chain_type="map_reduce",
        map_prompt=PromptTemplate(
            input_variables=["text"],
            template="""请总结以下文本内容:
                {text}
                总结:"""
        ),
        combine_prompt=PromptTemplate(
            input_variables=["text"],
            template="""请将以下摘要合并为一个连贯的总结:
                {text}
                最终总结:"""
        )
    )
    # 执行摘要
    shortened_text = summary_chain.invoke({"input_documents": docs})
    print(f"摘要生成完成，长度: {len(shortened_text)} 字符")
    return {"output_text": shortened_text}


def main():
    # 使用上述转换函数创建一个TransformChain对象。
    # 定义输入变量为["text"]，输出变量为["output_text"]，并指定转换函数为transform_func。
    # 提供一个壳子 将函数处理能力
    transform_chain = TransformChain(
        input_variables=["raw_text"], output_variables=["output_text"], transform=transform_func
    )
    # 通过chain转换后的文本数据 包括两个key raw_text输入结果 output_text输出结果
    transformed_novel = transform_chain.invoke({"raw_text": novel_text})
    print(transformed_novel)

    template = """总结下面文本:
    {output_text}
    总结:"""
    prompt = PromptTemplate(input_variables=["output_text"], template=template)
    llm_chain = (
            RunnablePassthrough()  # 传递输入
            | prompt  # 应用 prompt
            | DashScopeAI(streaming=True)  # 流式调用
    )
    few_output_text = transformed_novel['output_text']
    # 使用流式输出的方式获取LLM结果
    print("\n--- 开始生成总结 ---")
    result = llm_chain.stream({"output_text": few_output_text})
    for chunk in result:
        print(chunk, end='', flush=True)
        print()


if __name__ == "__main__":
    main()
