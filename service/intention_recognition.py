from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from config.base_config_dashscope import BASHSCOPE_MODEL_NAME
from models.llms.llms_adapter import LLMsAdapter


class LLMIntentClassifier:
    """基于大语言模型的意图分类器"""

    # 调用大模型判断用户意图的提示词常量
    LLM_PROMPT_TEMPLATE = """
    你是一个专业的意图分类器。请根据用户的问题，判断其意图是否与医学或生命科学领域（包括基础医学、临床医学、生物学、预防医学与卫生学、药学、中医学与中药学）相关。
    判断标准：
    符合医学相关的场景：
    - 涉及疾病的病因、症状、诊断、治疗、预防等（如 “头痛怎么办”“高血压用药”）。
    - 提及医疗器械、疫苗、医保政策、母婴 / 心理卫生等（如 “胰岛素泵使用”“九价疫苗预约”）。
    - 涉及疾病的机制，如解剖、细胞生物、生理、组织胚胎、遗传、免疫、微生物、病理、药理等
    - 涉及疾病的防控
    - 涉及中医对疾病诊疗的应用
    
    不符合医学相关的场景：
    - 纯社交闲聊（如 “你好”“今天天气如何”）。
    - 非医疗类咨询（如法律、教育、购物、交通等）。
    - 广告营销、恶意提问、无关灌水内容。
    
    如果用户的问题与医疗诊断相关，请回复"medical_diagnosis"。
    如果用户的问题与医疗诊断无关，请回复"other"。

    仅回复"medical_diagnosis"或"other"，不添加任何其他内容。

    用户问题：{user_input}
    """

    def __init__(self, model: str = "DashScope", model_name: str = BASHSCOPE_MODEL_NAME):
        """
        初始化大语言模型意图分类器
        :param model: 大模型
        :param model_name: 模型名称
        """
        adapter = LLMsAdapter(model=model, model_name=model_name)
        # llm = adapter.get_model_instance()
        llm = adapter.get_chat_model_instance(history=[])
        # 封装指令信息
        prompt = PromptTemplate(
            template=self.LLM_PROMPT_TEMPLATE,
            input_variables=["user_input"]
        )
        parser = StrOutputParser()
        self.chain = prompt | llm | parser


    def classify(self, user_input: str) -> str:
        """
        根据大模型判断用户意图
        :param user_input: 用户输入文本
        :return: 匹配的意图类别
        """
        try:
            model_response = self.chain.invoke(user_input)
            model_response = model_response.strip()
            # 验证回复格式
            if model_response == "medical_diagnosis":
                return "medical_diagnosis"
            elif model_response == "other":
                return "other"

            # 如果回复格式不符合预期，记录并返回默认值
            print(f"警告: 模型返回意外格式: {model_response}")
            return "other"

        except Exception as e:
            print(f"大模型调用错误: {e}")
            return "other"

class MedicalDiagnosisChecker:
    """医疗诊断检查器，用于判断用户问题是否与医疗诊断相关"""

    # 非医疗相关问题的固定回答常量
    FIXED_RESPONSE = (
        "医知立方聚焦医学答疑，请提问医学及生命科学相关问题"
    )

    def __init__(self, model: str = "DashScope", model_name: str = BASHSCOPE_MODEL_NAME):
        """
        初始化医疗诊断检查器
        :param model: 大模型A
        :param model_name: 模型名称
        """
        # 创建大模型意图分类器
        self.intent_classifier = LLMIntentClassifier(model, model_name)

    def check_medical_intent(self, user_input: str) -> bool:
        """
        检查用户输入是否与医疗诊断相关
        :param user_input: 用户输入文本
        :return: 如果相关返回True，否则返回False
        """
        return self.intent_classifier.classify(user_input) == "medical_diagnosis"

    def get_response(self, user_input: str) -> str:
        """
        根据用户输入获取相应回复
        :param user_input: 用户输入文本
        :return: 如果是医疗相关问题返回None，否则返回固定回答
        """
        if self.check_medical_intent(user_input):
            return None  # 医疗相关问题将由其他模块处理
        return self.FIXED_RESPONSE

# 使用示例
if __name__ == "__main__":
    checker = MedicalDiagnosisChecker(model="DashScope", model_name=BASHSCOPE_MODEL_NAME)
    # checker = MedicalDiagnosisChecker(model="Deepseek", model_name="deepseek-chat")

    # 测试问题
    test_questions = [
        "我头痛发烧怎么办？",          # 医疗相关
        "高血压需要吃什么药？",        # 医疗相关
        "糖尿病的早期症状有哪些？",    # 医疗相关
        "今天天气如何？",              # 非医疗
        "推荐一部好看的电影",          # 非医疗
        "如何学习Python编程？",         # 非医疗
        "披裂在医学上的含义？",         # 非医疗
        "如何学习临床医学？"         # 医疗相关
    ]

    # 执行测试
    print("=== 意图分类测试 ===")
    for question in test_questions:
        print(f"问题: {question}")
        response = checker.get_response(question)
        # response = chain.invoke(question)
        print(f"回答: {response if response else '（将由医疗模块处理）'}")
        print()    