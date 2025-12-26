from langchain_community.tools import TavilySearchResults

from config.base_config import TAVILY_API_KEY


class SearchService:
    """
    搜索相关
        - tavily搜索
    """

    search = None

    def __init__(self):
        self.search = TavilySearchResults(max_results=5, tavily_api_key=TAVILY_API_KEY)

    def get_tavily_search_list(self, query: str):
        """
        获取tavily搜索列表
        :param query: 搜索内容
        :return: 搜索相关列表
        """
        input_results = []
        query_results = self.search.run(query)
        for result in query_results:
            input_results.append(result.get("content"))
        return input_results, query_results


if __name__ == '__main__':
    SearchService().get_tavily_search_list(query="今天天气如何")
