from typing import List


class BusinessCode:

    def __init__(self, code: int, message: str):
        """
        构造函数
        :param code: 异常代码
        :param message: 异常信息
        """
        self.code = code
        self.message = message

    def __repr__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "异常代码["+str(self.code)+"]"


def get_fastapi_model(error_list: List[BusinessCode]):
    """
    封装Fastapi异常返回模型
    :param error_list: 异常代码列表
    :return: 异常返回
    """
    examples = {}
    num = 900
    for e in error_list:
        examples[num] = {
            "content": {
                "application/json": {
                    "example": {
                        "status": e.code,
                        "message": e.message,
                        "data": None,
                    }
                }
            },
            "description": "异常代码示例.",
        }
        num = num + 1
    return examples


'''
机器人模块
'''
ERROR_10000 = BusinessCode(10000, "未查询到机器人信息")
ERROR_10001 = BusinessCode(10001, "未查询到所属知识库信息")
ERROR_10002 = BusinessCode(10002, "Prompt指令信息不合法")
ERROR_10006 = BusinessCode(10006, "当前机器人的所属类型不合法")
ERROR_10007 = BusinessCode(10007, "当前机器人的使用类型不合法")
ERROR_10008 = BusinessCode(10008, "提示词缺少占位符信息")
'''
知识库模块
'''
ERROR_10201 = BusinessCode(10201, "查询向量库文档操作失败")
ERROR_10202 = BusinessCode(10202, "查询业务背景的向量库文档操作失败")
ERROR_10203 = BusinessCode(10203, "查询风格背景的向量库文档操作失败")
ERROR_10204 = BusinessCode(10204, "查询业务背景的向量库文档不能为空")
ERROR_10205 = BusinessCode(10205, "查询风格背景的向量库文档不能为空")
ERROR_10206 = BusinessCode(10206, "解析预制文件CSV失败")
ERROR_10207 = BusinessCode(10207, "指定文件所属知识库标识不匹配")
ERROR_10208 = BusinessCode(10208, "文件加载异常，参数不全")
ERROR_10209 = BusinessCode(10209, "知识库文件标识不能为空")
ERROR_10210 = BusinessCode(10210, "未查询到知识库文件信息")
ERROR_10211 = BusinessCode(10211, "解析Excel文件失败")
ERROR_10212 = BusinessCode(10212, "未查询到当前分片信息")
ERROR_10213 = BusinessCode(10213, "知识库文件的向量化状态异常，不可执行向量化操作")
'''
演讲稿模块
'''
ERROR_10300 = BusinessCode(10300, "未查询到指定业务背景知识库信息")
ERROR_10301 = BusinessCode(10301, "未查询到指定风格背景知识库信息")
'''
定制化模型
'''
ERROR_10900 = BusinessCode(10900, "请求大模型API超时")
ERROR_10901 = BusinessCode(10901, "请求千帆大模型获取AccessToken失败")
ERROR_10902 = BusinessCode(10902, "请求千帆大模型聊天对话失败")
ERROR_10910 = BusinessCode(10910, "未查询到图片生成信息")
ERROR_10911 = BusinessCode(10911, "大模型训练操作异常")
ERROR_10912 = BusinessCode(10912, "大模型推理操作异常")
