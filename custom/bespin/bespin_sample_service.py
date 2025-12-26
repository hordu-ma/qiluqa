import random
import re
import traceback
import uuid
from typing import List

from langchain_core.prompts import PromptTemplate

from custom.bespin.amap.amap_client import AmapClient
from framework.util.dict_util import DictUtil
from models.chains.chain_model import ChainModel
from models.llms.llms_adapter import LLMsAdapter
from service.base_chat_message import BaseChatMessage
from service.domain.ai_chat_bot import ChatBotModel
from loguru import logger

prompt_template_nn = """
请根据用户问题以及历史聊天记录进行意图识别，我会提供一个参考示例，你只需要回答‘是’/‘否’，请按照要求将识别结果填充到占位符结构体，分析不出来可以为空，但不能编造非参考示例的其它标签。

参考示例
'''
用户想要查询天气<weather>是</weather>
用户想要查询美食推荐<food>是</food>
用户想要查询附近停车场<parking>是</parking>
用户想要查询附近高速服务区<expresswayServiceArea>是</expresswayServiceArea>
用户想要查询附近充电桩<charger>是</charger>
用户想要行车导航<navigation>是</navigation>
用户想要个人行程规划<direction>是</direction>
用户问题中提到的行政市<city>广州市西门口</city>
用户问题中提到想要去的地理位置<address>广州市天河区正佳广场</address>
'''

注意事项
'''
1.若<navigation>标签值为‘是’时，请务必返回<address>标签。
2.若<direction>标签值为‘是’时，请务必结合历史聊天记录总结出用户的行程安排以及注意事项，并将结果写入<result>标签，参考格式如下所示：
```markdown
 - 下班后充电:
   -- 门店:
   -- 地址：
   -- 费用：
   -- 电量：
   -- 充电时间：
  - 去吃饭:
   -- 餐厅:
   -- 地址:
   -- 路线:
   -- 费用:
  - 看电影：
   -- 影院:
   -- 地址:
   -- 到达时间:
  - 行车导航:
   -- 路线:
   -- 到达时间:
```
'''

用户问题
'''
{question}
'''

"""
prompt_template_nn_var = ['question']


prompt_template_kk = """
请根据用户问题以及历史聊天记录进行意图识别，我会提供一个参考示例，你只需要回答‘是’/‘否’，请按照要求将识别结果填充到占位符结构体，分析不出来可以为空，但不能编造非参考示例的其它标签。

参考示例
'''
用户想要查询天气<weather>是</weather>
用户想要查询4S店<car>是</car>
用户想要查询车损信息<vehicle>是</vehicle>
'''

注意事项
'''

'''

用户问题
'''
{question}
'''

"""
prompt_template_kk_var = ['question']


class SampleService:

    def __init__(
            self,
            request_id: str = str(uuid.uuid4()),
    ):
        """
        构造方法
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def plugin(
            self,
            ques: str,
            chatBotModel: ChatBotModel,
            history: List[List[str]] = None,
    ):
        sub_ques = ques
        try:
            bot_id = chatBotModel.bot_id
            # 行程规划定制机器人
            if bot_id == '790e85d9943442cfb9cf3ef15ebe4c26':
                logger.info("SampleService INFO, request_id={}, 当前机器人信息：{}.", self.request_id, chatBotModel)
                prompt_template = PromptTemplate(
                    template=prompt_template_nn,
                    input_variables=prompt_template_nn_var
                )
                chain = ChainModel.get_instance_with_llm_chain(
                    llm=LLMsAdapter(model="DashScope", model_name="qwen-max").get_model_instance(history=history),
                    prompt_template=prompt_template,
                    verbose=True
                )
                answer = chain.predict(question=ques)
                print(answer)
                answer_tap_dict = self.get_answer_tap_dict(answer)
                print(answer_tap_dict)
                weather = answer_tap_dict.get('weather') or ""
                weather = True if '是' in weather else False
                food = answer_tap_dict.get('food') or ""
                food = True if '是' in food else False
                parking = answer_tap_dict.get('parking') or ""
                parking = True if '是' in parking else False
                charger = answer_tap_dict.get('charger') or ""
                charger = True if '是' in charger else False
                navigation = answer_tap_dict.get('navigation') or ""
                navigation = True if '是' in navigation else False
                direction = answer_tap_dict.get('direction') or ""
                direction = True if '是' in direction else False
                expresswayServiceArea = answer_tap_dict.get('expresswayServiceArea') or ""
                expresswayServiceArea = True if '是' in expresswayServiceArea else False

                # 根据意图识别结果查询实时资讯
                if weather:
                    city = answer_tap_dict.get('city')
                    city = city if city and '空' != city else "广州市"
                    result = AmapClient(request_id=self.request_id).weather(city=city)
                    if not result:
                        return ques, sub_ques
                    amap_result = f"高德天气查询信息: {result}"
                    amap_result = str(amap_result).replace("{", "(").replace("}", ")")
                    # 提示词占位符处理
                    BaseChatMessage.placeholder(
                        chatBotModel=chatBotModel,
                        request_id=self.request_id,
                        is_want_delete=True,
                        amap_result=amap_result,
                    )
                elif food:
                    result = AmapClient(request_id=self.request_id).search_place_with_around(city="广州", keywords="美食推荐")
                    if not result:
                        return ques, sub_ques
                    amap_result = self.handle_amap_result(result, "food")
                    amap_result = f"高德美食推荐信息: {amap_result} \n以上信息为广州市越秀区西门口附近的门店推荐。"
                    # 提示词占位符处理
                    BaseChatMessage.placeholder(
                        chatBotModel=chatBotModel,
                        request_id=self.request_id,
                        is_want_delete=True,
                        amap_result=amap_result,
                    )
                    sub_ques = ques + "，请帮我多推荐几家门店"
                elif parking:
                    result = AmapClient(request_id=self.request_id).search_place_with_around(city="广州", keywords="停车场")
                    if not result:
                        return ques, sub_ques
                    amap_result = self.handle_amap_result(result, "parking")
                    amap_result = f"高德停车场推荐信息: {amap_result} \n以上信息为广州市越秀区西门口附近的停车场推荐。"
                    # 提示词占位符处理
                    BaseChatMessage.placeholder(
                        chatBotModel=chatBotModel,
                        request_id=self.request_id,
                        is_want_delete=True,
                        amap_result=amap_result,
                    )
                    sub_ques = ques + "，请帮我多推荐几家停车场"
                elif direction:
                    amap_result = answer_tap_dict.get('result')
                    if not amap_result:
                        return ques, sub_ques
                    amap_result = f"高德实时行程规划信息: {amap_result} \n以上行程安排是根据用户历史聊天生成。"
                    # 提示词占位符处理
                    BaseChatMessage.placeholder(
                        chatBotModel=chatBotModel,
                        request_id=self.request_id,
                        is_want_delete=True,
                        amap_result=amap_result,
                    )
                elif navigation:
                    address = answer_tap_dict.get('address')
                    address = address if address and '空' != address else "广州市西门口"
                    amapClient = AmapClient(request_id=self.request_id)
                    x, y, addr = amapClient.transformer(cus_address=address)
                    if not x or not y:
                        return ques, sub_ques
                    if x and y and addr:
                        direction_result = amapClient.direction(destination=x + "," + y)
                        if not direction_result:
                            return ques, sub_ques
                        direction_result = dict(direction_result)
                        steps = []
                        for step in direction_result["steps"]:
                            step = dict(step)
                            del step["tmcs"]
                            del step["polyline"]
                            del step["tolls"]
                            del step["toll_distance"]
                            del step["toll_road"]
                            del step["assistant_action"]
                            steps.append(step)
                        if len(steps) > 4:
                            steps_start = steps[:3]
                            steps_end = steps[(len(steps)-1):]
                            steps = list(steps_start) + list(steps_end)
                        direction_result["steps"] = steps
                        direction_result = str(direction_result).replace("{", "(").replace("}", ")")
                        amap_result = f"高德路径规划信息: {direction_result}"
                        amap_result = str(amap_result).replace("{", "(").replace("}", ")").replace("'", "\'")
                        # 提示词占位符处理
                        BaseChatMessage.placeholder(
                            chatBotModel=chatBotModel,
                            request_id=self.request_id,
                            is_want_delete=True,
                            amap_result=amap_result,
                        )
                elif charger:
                    result = AmapClient(request_id=self.request_id).search_place_with_around(city="广州", keywords="充电桩")
                    if not result:
                        return ques, sub_ques
                    amap_result = self.handle_amap_result(result, "charger")
                    amap_result = f"高德充电桩推荐信息: {amap_result} \n以上信息为广州市越秀区西门口附近的充电桩推荐。"
                    # 提示词占位符处理
                    BaseChatMessage.placeholder(
                        chatBotModel=chatBotModel,
                        request_id=self.request_id,
                        is_want_delete=True,
                        amap_result=amap_result,
                    )
                    sub_ques = ques + "，请帮我多推荐几家充电桩"
                elif expresswayServiceArea:
                    result = AmapClient(request_id=self.request_id).search_place_with_around(city="广州", keywords="高速服务区")
                    if not result:
                        return ques, sub_ques
                    amap_result = self.handle_amap_result(result, "charger")
                    amap_result = f"高德高速服务区推荐信息: {amap_result} \n以上信息为广州市高速服务区推荐。"
                    # 提示词占位符处理
                    BaseChatMessage.placeholder(
                        chatBotModel=chatBotModel,
                        request_id=self.request_id,
                        is_want_delete=True,
                        amap_result=amap_result,
                    )
                    sub_ques = ques + "，请帮我多推荐几个高速服务区"

            elif bot_id == '3b17f39920d145628b4a7fd1e3de23f0':
                logger.info("SampleService INFO, request_id={}, 当前机器人信息：{}.", self.request_id, chatBotModel)
                prompt_template = PromptTemplate(
                    template=prompt_template_kk,
                    input_variables=prompt_template_kk_var
                )
                chain = ChainModel.get_instance_with_llm_chain(
                    llm=LLMsAdapter(model="DashScope", model_name="qwen-max").get_model_instance(history=history),
                    prompt_template=prompt_template,
                    verbose=True
                )
                answer = chain.predict(question=ques)
                print(answer)
                answer_tap_dict = self.get_answer_tap_dict(answer)
                print(answer_tap_dict)
                if DictUtil.get_intention_with_bool(answer_tap_dict, "vehicle"):
                    amap_result = (f"车主的车辆实时信息: \n用户本人车辆品牌：现代 \n用户本人车辆型号：索纳塔 \n"
                                   f"用户本人车辆实时位置：广东省广州市白云区京广高速 \n用户本人车辆故障码信息：前左轮轮胎气压低、刹车故障")
                    # 提示词占位符处理
                    BaseChatMessage.placeholder(
                        chatBotModel=chatBotModel,
                        request_id=self.request_id,
                        is_want_delete=True,
                        amap_result=amap_result,
                    )
                elif DictUtil.get_intention_with_bool(answer_tap_dict, "car"):
                    result = AmapClient(request_id=self.request_id).assistant(city="广州", keywords="北京现代4s店")
                    if not result:
                        return ques, sub_ques
                    amap_result = self.handle_amap_result(result, "car")
                    amap_result = f"高德4S店推荐信息: {amap_result} \n以上信息为广州市附近的北京现代4s店推荐。"
                    # 提示词占位符处理
                    BaseChatMessage.placeholder(
                        chatBotModel=chatBotModel,
                        request_id=self.request_id,
                        is_want_delete=True,
                        amap_result=amap_result,
                    )
                    sub_ques = ques + "，请帮我优先推荐北京现代4S店，且多推荐几个选择。"
        except Exception as err:
            traceback.print_exc()
            logger.error("SampleService ERROR, request_id={}, err={}", self.request_id, err)

        BaseChatMessage.placeholder(
            chatBotModel=chatBotModel,
            request_id=self.request_id,
            is_want_delete=True,
        )
        return ques, sub_ques

    @classmethod
    def get_answer_tap_dict(cls, answer: str):
        """
        使用正则表达式获取回答中的所有标签内的信息
        并以该标签和信息组成字典
        """
        if not answer:
            return {}
        matches = re.findall(r'<([\w\u4e00-\u9fa5]+)[^>]*>([\s\S]*?)(?=</\1>|<[\w\u4e00-\u9fa5]+>|$)', answer)
        answer_dict = {}
        for match in matches:
            tag = match[0]
            value = match[1]
            answer_dict[tag] = value
        return answer_dict

    def handle_amap_result(self, amap_result: dict, amap_result_type: str) -> str:
        if "food" in amap_result_type:
            result = ""
            for poi in list(amap_result["pois"]):
                poi = dict(poi)
                temp = (
                        "\n店家：" + poi["name"] +
                        "\n地址：" + (poi["address"] if poi["address"] else "") +
                        "\n评分：" + str(self.rrr()) +
                        "\n用户评价：" + self.ppp() +
                        "\n\n"
                        )
                result = result + temp
            return result
        elif "parking" in amap_result_type:
            result = ""
            for poi in list(amap_result["pois"]):
                poi = dict(poi)
                temp = (
                        "\n店家：" + poi["name"] +
                        "\n地址：" + (poi["address"] if poi["address"] else "") +
                        "\n\n"
                )
                result = result + temp
            return result
        elif "charger" in amap_result_type:
            result = ""
            for poi in list(amap_result["pois"]):
                poi = dict(poi)
                temp = (
                        "\n店家：" + poi["name"] +
                        "\n地址：" + (poi["address"] if poi["address"] else "") +
                        "\n\n"
                )
                result = result + temp
            return result
        elif "car" in amap_result_type:
            result = ""
            for tip in list(amap_result["tips"]):
                tip = dict(tip)
                temp = (
                        "\n店家：" + tip["name"] +
                        "\n区域：" + (tip["district"] if tip["district"] else "") +
                        "\n地址：" + (tip["address"] if tip["address"] else "") +
                        "\n\n"
                )
                result = result + temp
            return result
        return ""

    @classmethod
    def rrr(cls):
        return random.choice([4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5.0])

    @classmethod
    def ppp(cls):
        return random.choice([
            "味道超级棒，色香味俱全，吃了之后感觉胃特别舒服",
            "菜品新鲜，口感细腻，味道非常好，令人回味无穷",
            "价格实惠，味道正宗，环境优美，服务周到，非常满意",
            "菜品丰富多样，口感鲜美，性价比高，让人流连忘返",
            "店家服务态度非常好，让人感觉特别舒服，下次还会再来",
            "菜品新鲜健康，烹饪技艺高超，让人食欲大增，非常值得推荐",
            "价格实惠，味道好，分量足，是一家值得多次光顾的美食店",
            "这家餐厅的菜肴真是太美味了，每一道菜都让我感到惊喜！强烈推荐！"
            "我对这家餐厅的菜肴赞不绝口，口感细腻，食材新鲜，绝对物超所值"
        ])


if __name__ == "__main__":
    chatBotModel = ChatBotModel(data=('','','','','','','','','','','','','','','','','','','','','','','','','','','','','','','',''))
    chatBotModel.bot_id = '790e85d9943442cfb9cf3ef15ebe4c26'
    # chatBotModel.bot_id = '3b17f39920d145628b4a7fd1e3de23f0'
    print(SampleService().plugin(ques="周围有高速服务区吗？", chatBotModel=chatBotModel))
    print(chatBotModel)
    # SampleService().plugin(ques="怎么去中山七路", chatBotModel=chatBotModel)
    # SampleService().plugin(ques="广州市今天天气如何？", chatBotModel=chatBotModel)
    pass
