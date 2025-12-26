import uuid

import requests
from custom.bespin.amap.amap_config import AMAP_KEY, AMAP_ORIGIN_LOCATION


class AmapClient:

    def __init__(
            self,
            key: str = AMAP_KEY,
            request_id: str = str(uuid.uuid4())
    ):
        self.key = key
        self.request_id = request_id
        self.types = "050000|070000|150000"

    def transformer(
            self,
            cus_address: str
    ):
        """
        获取地理位置信息以及经纬度
        @see amap_sample
        """
        url = f"https://restapi.amap.com/v3/geocode/geo?key={self.key}&address={cus_address}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1':
                geo = data['geocodes'][0]
                return geo['location'].split(',')[0], geo['location'].split(',')[1], data
        return None, None, None

    def direction(
            self,
            destination: str,
            origin: str = AMAP_ORIGIN_LOCATION,
    ):
        """
        驾车路径规划
        @see amap_sample
        """
        url = f'https://restapi.amap.com/v3/direction/driving?origin={origin}&destination={destination}&key={self.key}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # print("AmapClient direction INFO, response={}", data['route']['paths'][0])
            if data['status'] == '1':
                return data['route']['paths'][0]
        return None

    def weather(self, city: str):
        """
        查询天气信息
        @see amap_sample
        """
        url = f'https://restapi.amap.com/v3/weather/weatherInfo?city={city}&key={self.key}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("AmapClient weather INFO, response={}", data)
            if data['status'] == '1' and data['lives']:
                return data['lives'][0]
        return None

    def search_place_with_keyword(
            self,
            city: str,
            keywords: str,
            page: int = 1,
            offset: int = 24
    ):
        """
        关键字搜索
        """
        url = (f'https://restapi.amap.com/v3/place/text?key={self.key}'
               f'&city={city}&keywords={keywords}&types={self.types}&page={page}&offset={offset}')
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1':
                return data
        return None

    def search_place_with_around(
            self,
            city: str,
            keywords: str,
            page: int = 1,
            offset: int = 24,
            location: str = AMAP_ORIGIN_LOCATION,
    ):
        """
        周边搜索
        """
        url = (f'https://restapi.amap.com/v3/place/around?key={self.key}'
               f'&city={city}&keywords={keywords}&types={self.types}&page={page}&offset={offset}&location={location}')
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1':
                return data
        return None

    def assistant(
            self,
            city: str,
            keywords: str,
    ):
        """
        输入提示
        """
        url = (f'https://restapi.amap.com/v3/assistant/inputtips?key={self.key}'
               f'&city={city}&keywords={keywords}&citylimit=true')
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1':
                return data
        return None


if __name__ == "__main__":
    cus_address = "广州"
    # x, y, addr = AmapClient().transformer(cus_address=cus_address)
    # print(x, y, addr)
    # result = AmapClient().direction(destination=x + "," + y)
    # result = AmapClient().weather(city=cus_address)
    # result = AmapClient().search_place_with_keyword(city=cus_address, keywords="美食")
    # result = AmapClient().search_place_with_around(city=cus_address, keywords="现代汽车")
    result = AmapClient().assistant(city=cus_address, keywords="北京现代4s店")
    print(result)
    pass
